import requests
import pytest

@pytest.fixture(scope='module')
def base_url():
    return "http://localhost:8000"

@pytest.fixture(scope='module')
def test_patient(base_url):
    payload = {"name": "testName", "age": 30}
    response = requests.post(f"{base_url}/patients/", json=payload)
    assert response.status_code == 200, response.text
    return response.json()

def test_create_patient(base_url):
    payload = {"name": "nameTest", "age": 25}
    response = requests.post(f"{base_url}/patients/", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data['name'] == "nameTest"
    assert data['age'] == 25

def test_read_patient(base_url, test_patient):
    patient_id = test_patient['id']
    full_url = f"{base_url}/patients/{patient_id}"
    response = requests.get(full_url)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data['id'] == patient_id
    assert data['name'] == "testName"
    assert data['age'] == 30
