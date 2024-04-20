from fastapi import FastAPI, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from typing import List
from datetime import date
from starlette_prometheus import PrometheusMiddleware, metrics
import httpx
import logging

DATABASE_URL = "postgresql://micros_user:1987@host.docker.internal:5432/micros_database"

Base = declarative_base()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
app.add_route("/metrics", metrics)

def get_db():
    db = SessionLocal()
    logger.debug("Database connection opened")
    try:
        yield db
    finally:
        db.close()
        logger.debug("Database connection closed")

@app.post("/patients/", response_model=PatientSchema)
def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    try:
        db_patient = Patient(name=patient.name, age=patient.age)
        db.add(db_patient)
        db.commit()
        db.refresh(db_patient)
        logger.info(f"New patient created: {db_patient.name}")
        return db_patient
    except Exception as e:
        logger.error(f"Error creating patient: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get/{patient_id}", response_model=List[Appointment])
async def fetch_appointments_for_patient(patient_id: int = Path()):
    logger.info(f"Fetching appointments for patient_id: {patient_id}")
    url = f"https://bba0qda4f9bhjf2ivkr8.containers.yandexcloud.net/appointments/{patient_id}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        if response.status_code != 200:
            logger.error(f"Failed to fetch appointments: {response.status_code}")
            raise HTTPException(status_code=response.status_code, detail="Error fetching external data")
        logger.info(f"Appointments fetched successfully for patient_id: {patient_id}")
        all_appointments = response.json()
        filtered_appointments = [Appointment(**appointment) for appointment in all_appointments if appointment['patient_id'] == patient_id]
        return filtered_appointments
