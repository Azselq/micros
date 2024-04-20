from fastapi import APIRouter, FastAPI, Depends, HTTPException, Path, status, Form
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from typing import List
from datetime import date
import httpx
import requests
from keycloak import KeycloakOpenID
from fastapi.security import OAuth2AuthorizationCodeBearer, SecurityScopes
from starlette_exporter import PrometheusMiddleware, handle_metrics
import logging

DATABASE_URL="postgresql://micros_user:1987@host.docker.internal:5432/micros_database"

Base = declarative_base()

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    age = Column(Integer)

class Appointment(BaseModel):
    patient_id: int
    date: date

class PatientCreate(BaseModel):
    name: str
    age: int

class PatientSchema(PatientCreate):
    id: int

    class Config:
        orm_mode = True

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI()


app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", handle_metrics)


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

KEYCLOAK_URL = "http://localhost:8080"
KEYCLOAK_REALM = "realm"
KEYCLOAK_CLIENT_ID = "test"
KEYCLOAK_CLIENT_SECRET = "3dFOWjFf0HZUSSfiDvXAO2Zmt6cJ5y6I"
keycloak_openid = KeycloakOpenID(server_url=KEYCLOAK_URL,
                                 client_id=KEYCLOAK_CLIENT_ID,
                                 realm_name=KEYCLOAK_REALM,
                                 client_secret_key=KEYCLOAK_CLIENT_SECRET)

oauth2_scheme = OAuth2AuthorizationCodeBearer(
    authorizationUrl=f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/auth",
    tokenUrl=f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token"
)

def get_current_user(security_scopes: SecurityScopes, token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        decoded_token = keycloak_openid.decode_token(token, key=KEYCLOAK_CLIENT_SECRET)
        if not decoded_token['scope'] in security_scopes.scopes:
            raise HTTPException(status_code=403, detail="Not enough permissions")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")
    return decoded_token

@app.post("/login")
def login_for_access_token(username: str = Form(...), password: str = Form(...)):
    token_response = get_token_from_keycloak(username, password)
    if token_response.status_code == 200:
        return token_response.json()
    else:
        raise HTTPException(status_code=token_response.status_code, detail="Keycloak authentication failed")

def get_token_from_keycloak(username: str, password: str):
    data = {
        'client_id': KEYCLOAK_CLIENT_ID,
        'client_secret': KEYCLOAK_CLIENT_SECRET,
        'username': username,
        'password': password,
        'grant_type': 'password'
    }
    token_url = f"{KEYCLOAK_URL}/realms/{KEYCLOAK_REALM}/protocol/openid-connect/token"
    logger.info(f"Requesting token from Keycloak for user {username}")
    response = requests.post(token_url, data=data)
    if response.status_code != 200:
        logger.error(f"Failed to get token from Keycloak for user {username}. Status code: {response.status_code}")
    return response

@app.post("/patients/", response_model=PatientSchema)
def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    db_patient = Patient(name=patient.name, age=patient.age)
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

@app.get("/patients/{patient_id}", response_model=PatientSchema)
def read_patient(patient_id: int, db: Session = Depends(get_db)):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

router = APIRouter()

@app.get("/get/{patient_id}", response_model=List[Appointment])
async def fetch_appointments_for_patient(patient_id: int = Path()):
    url = "https://bba0qda4f9bhjf2ivkr8.containers.yandexcloud.net/appointments"
    async with httpx.AsyncClient() as client:
        response = await client.get(url + f"/{patient_id}")
        if response.status_code != 200:
            logger.error(f"Failed to fetch appointments for patient {patient_id} from external service. Status code: {response.status_code}")
            raise HTTPException(status_code=response.status_code, detail="Error fetching external data")
        all_appointments = response.json()
        filtered_appointments = [Appointment(**appointment) for appointment in all_appointments if appointment['patient_id'] == patient_id]
        return filtered_appointments

app.include_router(router)