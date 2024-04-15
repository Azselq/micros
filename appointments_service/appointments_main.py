from fastapi import FastAPI, HTTPException
from datetime import date, timedelta
from typing import List
import requests
import uvicorn
import os

app = FastAPI()

patients_data = [
    {"id": 1, "name": "Александр Александрович", "age": 35},
    {"id": 2, "name": "Александр Александрович", "age": 35},
    {"id": 3, "name": "Александр Александрович", "age": 35},
    {"id": 4, "name": "Александр Артемович", "age": 23},
    {"id": 5, "name": "Кирилл Максимович", "age": 20}
]
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
def create_appointment(patient_id: int, appointment_date: date):
    response = requests.get(f"http://patients_service:8000/patients/{patient_id}")
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail="Patient not found")
    appointment = {"patient_id": patient_id, "date": appointment_date}
    appointments.append(appointment)
    return appointment

@app.get("/")
def get_appointments():
    return appointments

if __name__ == "__main__":
    uvicorn.run("appointments_main:app", host="0.0.0.0", port=int(os.getenv('PORT', 8001)))
