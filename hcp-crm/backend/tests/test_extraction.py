import pytest

from app.services.groq_service import ExtractionError, validate_and_clean
from app.schemas.extraction import ExtractedPatient

SAMPLE = (
    "Patient John, 45 years old, male, visited the hospital with fever and headache. "
    "Diagnosed with viral fever. Assigned to Dr. Kumar."
)


# ---------- validation logic (no network, no Groq key needed) ----------
def test_expected_example_output():
    raw = {
        "patient_name": "John", "age": 45, "gender": "Male", "symptoms": "Fever and headache",
        "diagnosis": "Viral fever", "doctor_assigned": "Dr. Kumar",
    }
    r = validate_and_clean(raw, SAMPLE)
    assert r.patient_name == "John" and r.age == 45 and r.gender == "Male"
    assert r.symptoms == "Fever and headache" and r.diagnosis == "Viral fever"
    assert r.doctor_assigned == "Dr. Kumar"
    assert r.phone is None and r.email is None and r.appointment_date is None


def test_invented_contact_details_are_dropped():
    raw = {"patient_name": "John", "phone": "9876543210", "email": "john@x.com", "appointment_date": "tomorrow"}
    r = validate_and_clean(raw, SAMPLE)
    assert r.phone is None and r.email is None and r.appointment_date is None


def test_contact_details_kept_when_present_in_text():
    text = "Priya Sharma, phone 98765 43210, email priya@example.com, seen on 2026-03-05."
    raw = {"patient_name": "Priya Sharma", "phone": "9876543210", "email": "priya@example.com",
           "appointment_date": "2026-03-05"}
    r = validate_and_clean(raw, text)
    assert r.phone == "9876543210" and r.email == "priya@example.com"
    assert str(r.appointment_date) == "2026-03-05"


def test_hallucinated_name_and_bad_values_become_null():
    r = validate_and_clean(
        {"patient_name": "Zed Quill", "age": 200, "gender": "robot", "diagnosis": "N/A", "symptoms": "null"}, SAMPLE
    )
    assert r.patient_name is None and r.age is None and r.gender is None
    assert r.diagnosis is None and r.symptoms is None


def test_non_dict_values_do_not_crash():
    r = validate_and_clean({"patient_name": ["John"], "age": {"x": 1}, "symptoms": True}, SAMPLE)
    assert isinstance(r, ExtractedPatient) and r.patient_name is None and r.age is None


# ---------- endpoint (Groq call is mocked) ----------
def test_extract_endpoint_success(client, auth, monkeypatch):
    fake = ExtractedPatient(patient_name="John", age=45, gender="Male", diagnosis="Viral fever")
    monkeypatch.setattr("app.routes.extract.extract_patient_info", lambda text: fake)
    res = client.post("/api/extract", json={"text": SAMPLE}, headers=auth)
    assert res.status_code == 200
    assert res.json()["extracted"]["patient_name"] == "John"
    assert res.json()["extracted"]["phone"] is None
    # extraction must NOT save anything
    assert client.get("/api/patients", headers=auth).json()["total"] == 0


@pytest.mark.parametrize("status", [429, 502, 503, 504])
def test_extract_endpoint_maps_errors(client, auth, monkeypatch, status):
    def boom(text):
        raise ExtractionError("AI problem", status)

    monkeypatch.setattr("app.routes.extract.extract_patient_info", boom)
    res = client.post("/api/extract", json={"text": SAMPLE}, headers=auth)
    assert res.status_code == status and res.json()["detail"] == "AI problem"


def test_extract_rejects_short_text(client, auth):
    assert client.post("/api/extract", json={"text": "hi"}, headers=auth).status_code == 422


def test_save_after_review_marks_source(client, auth):
    res = client.post("/api/patients", json={"full_name": "John", "age": 45, "source": "ai_extractor"}, headers=auth)
    assert res.status_code == 201 and res.json()["source"] == "ai_extractor"
