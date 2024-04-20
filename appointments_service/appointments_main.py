from fastapi import FastAPI, HTTPException
from datetime import date, timedelta
from typing import List
import requests
import uvicorn
import os
from pydantic import BaseModel

app = FastAPI()

patients_data = [
    {"id": 1, "name": "Александр Александрович", "age": 35},
    {"id": 2, "name": "Максим Петрович", "age": 35},
    {"id": 3, "name": "Ирина Вячеславовна", "age": 35},
    {"id": 4, "name": "Александр Артемович", "age": 23},
    {"id": 5, "name": "Кирилл Максимович", "age": 20}
]

class Appointment(BaseModel):
    patient_id: int
    date: date

def populate_appointments():
    today = date.today()
    for patient in patients_data:
        appointments.append({
            "patient_id": patient["id"],
            "date": today + timedelta(days=patient["id"])
        })

appointments = []
populate_appointments()


@app.post("/appointments/")
def create_appointment(appointment: Appointment):
    new_appointment = appointment.dict()
    appointments.append(new_appointment)
    return new_appointment

@app.get("/appointments/{patient_id}", response_model=List[Appointment])
def get_appointments_by_patient_id(patient_id: int):
    filtered_appointments = [appointment for appointment in appointments if appointment["patient_id"] == patient_id]
    if not filtered_appointments:
        raise HTTPException(status_code=404, detail="No appointments found for this patient")
    return filtered_appointments

@app.get("/", response_model=List[Appointment])
def get_appointments():
    return appointments

if __name__ == "__main__":
    uvicorn.run("appointments_main:app", host="0.0.0.0", port=int(os.getenv('PORT', 8001)))

