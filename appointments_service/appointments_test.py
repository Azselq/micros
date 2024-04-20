from fastapi.testclient import TestClient
from appointments_main import app, Appointment
from datetime import date
from pydantic import ValidationError
import pytest

client = TestClient(app)

def test_appointment_model():
    valid_appointment = {"patient_id": 1, "date": date.today()}
    try:
        Appointment(**valid_appointment)
        assert True
    except ValidationError:
        assert False
    invalid_appointment = {"patient_id": 1, "date": "20.04.2024"}
    with pytest.raises(ValidationError):
        Appointment(**invalid_appointment)

def test_create_appointment():
    response = client.post("/appointments/", json={"patient_id": 1, "date": str(date.today())})
    assert response.status_code == 200
    assert response.json() == {"patient_id": 1, "date": str(date.today())}


def test_get_appointments_by_patient_id():
    response = client.get("/appointments/1")
    assert response.status_code == 200
    assert type(response.json()) is list
    response = client.get("/appointments/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "No appointments found for this patient"}
