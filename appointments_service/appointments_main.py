

from fastapi import FastAPI, HTTPException
from datetime import date
from typing import List
import requests

app = FastAPI()

appointments = []

@app.post("/appointments/")
def create_appointment(patient_id: int, appointment_date: date):
    response = requests.get(f"http://patients_service:8000/patients/{patient_id}")
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Patient not found")
    appointment = {"patient_id": patient_id, "date": appointment_date}
    appointments.append(appointment)
    return appointment

@app.get("/appointments/")
def get_appointments():
    return appointments
