from fastapi import APIRouter, FastAPI, Depends, HTTPException, Path
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from typing import List
from datetime import date
import httpx

DATABASE_URL = "postgresql://micros_user:1987@db/micros_database"

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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/health")
async def health_check():
    return {"status": "up"}

@app.post("/patients/", response_model=PatientSchema)
def create_patient(patient: PatientCreate, db: Session = Depends(get_db)):
    db_patient = Patient(name=patient.name, age=patient.age)
    db.add(db_patient)
    db.commit()
    db.refresh(db_patient)
    return db_patient

@app.get("/patients/", response_model=List[PatientSchema])
def read_patients(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    patients = db.query(Patient).offset(skip).limit(limit).all()
    return patients

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
            raise HTTPException(status_code=response.status_code, detail="Error fetching external data")
        all_appointments = response.json()
        filtered_appointments = [Appointment(**appointment) for appointment in all_appointments if appointment['patient_id'] == patient_id]
        return filtered_appointments
app.include_router(router)
