from fastapi import FastAPI, HTTPException
from datetime import date, timedelta
from typing import List
import uvicorn
import os
import logging
from pydantic import BaseModel

from starlette_exporter import PrometheusMiddleware, handle_metrics

app = FastAPI()
app.add_middleware(PrometheusMiddleware)
app.add_route("/metrics", handle_metrics)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Patient(BaseModel):
    id: int
    name: str
    age: int

class Appointment(BaseModel):
    patient_id: int
    date: date

patients_data = [
    {"id": 1, "name": "Александр Александрович", "age": 35},
    {"id": 2, "name": "Максим Петрович", "age": 35},
    {"id": 3, "name": "Ирина Вячеславовна", "age": 35},
    {"id": 4, "name": "Александр Артемович", "age": 23},
    {"id": 5, "name": "Кирилл Максимович", "age": 20}
]

appointments = []

def populate_appointments():
    today = date.today()
    for patient in patients_data:
        appointment = {
            "patient_id": patient["id"],
            "date": today + timedelta(days=patient["id"])
        }
        appointments.append(appointment)
        logger.debug(f"Appointment populated: {appointment}")

populate_appointments()

@app.post("/appointments/")
def create_appointment(appointment: Appointment):
    new_appointment = appointment.dict()
    appointments.append(new_appointment)
    logger.info(f"New appointment created: {new_appointment}")
    return new_appointment

@app.get("/appointments/{patient_id}", response_model=List[Appointment])
def get_appointments_by_patient_id(patient_id: int):
    filtered_appointments = [appointment for appointment in appointments if appointment["patient_id"] == patient_id]
    if not filtered_appointments:
        logger.warning(f"No appointments found for patient_id {patient_id}")
        raise HTTPException(status_code=404, detail="No appointments found for this patient")
    logger.info(f"Appointments retrieved for patient_id {patient_id}: {filtered_appointments}")
    return filtered_appointments

@app.get("/", response_model=List[Appointment])
def get_appointments():
    logger.info("All appointments retrieved")
    return appointments

if __name__ == "__main__":
    logger.info("Starting server")
    uvicorn.run("appointments_main:app", host="0.0.0.0", port=int(os.getenv('PORT', 8001)))
