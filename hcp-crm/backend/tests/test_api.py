from datetime import date

from tests.conftest import FICTIONAL_PATIENT


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


# ---------- authentication ----------
def test_login_success(client):
    res = client.post("/api/auth/login", json={"username": "tester", "password": "secret123"})
    assert res.status_code == 200
    body = res.json()
    assert body["token_type"] == "bearer" and body["access_token"]
    assert body["user"]["username"] == "tester"


def test_login_wrong_password(client):
    res = client.post("/api/auth/login", json={"username": "tester", "password": "wrong"})
    assert res.status_code == 401


def test_protected_routes_need_token(client):
    for path in ("/api/patients", "/api/dashboard/stats", "/api/auth/me"):
        assert client.get(path).status_code == 401
    assert client.post("/api/extract", json={"text": "some medical text here"}).status_code == 401


def test_invalid_token_rejected(client):
    res = client.get("/api/patients", headers={"Authorization": "Bearer not-a-real-token"})
    assert res.status_code == 401


# ---------- patient CRUD ----------
def test_patient_crud_flow(client, auth):
    # create
    res = client.post("/api/patients", json=FICTIONAL_PATIENT, headers=auth)
    assert res.status_code == 201
    patient = res.json()
    assert patient["patient_code"] == f"HCP-{patient['id']:04d}"
    assert patient["gender"] == "Male"  # normalised
    pid = patient["id"]

    # read
    assert client.get(f"/api/patients/{pid}", headers=auth).json()["full_name"] == "Rahul Verma"

    # update only some fields
    res = client.put(f"/api/patients/{pid}", json={"diagnosis": "Recovered", "age": 46}, headers=auth)
    assert res.status_code == 200
    assert res.json()["diagnosis"] == "Recovered" and res.json()["age"] == 46
    assert res.json()["doctor_assigned"] == "Dr. Kumar"  # untouched

    # delete
    assert client.delete(f"/api/patients/{pid}", headers=auth).status_code == 204
    assert client.get(f"/api/patients/{pid}", headers=auth).status_code == 404


def test_patient_not_found(client, auth):
    assert client.get("/api/patients/9999", headers=auth).status_code == 404
    assert client.put("/api/patients/9999", json={"age": 1}, headers=auth).status_code == 404
    assert client.delete("/api/patients/9999", headers=auth).status_code == 404


def test_patient_validation(client, auth):
    bad_email = {**FICTIONAL_PATIENT, "email": "not-an-email"}
    assert client.post("/api/patients", json=bad_email, headers=auth).status_code == 422
    bad_gender = {**FICTIONAL_PATIENT, "gender": "robot"}
    assert client.post("/api/patients", json=bad_gender, headers=auth).status_code == 422
    bad_age = {**FICTIONAL_PATIENT, "age": 500}
    assert client.post("/api/patients", json=bad_age, headers=auth).status_code == 422
    assert client.post("/api/patients", json={"full_name": "  "}, headers=auth).status_code == 422


def test_blank_optional_fields_become_null(client, auth):
    res = client.post("/api/patients", json={"full_name": "Only Name", "phone": "", "email": ""}, headers=auth)
    assert res.status_code == 201
    assert res.json()["phone"] is None and res.json()["email"] is None


def test_search_and_pagination(client, auth):
    for i in range(12):
        client.post("/api/patients", json={"full_name": f"Patient {i:02d}", "diagnosis": "Fever"}, headers=auth)
    client.post("/api/patients", json={"full_name": "Special Case", "doctor_assigned": "Dr. Unique"}, headers=auth)

    page1 = client.get("/api/patients?limit=10", headers=auth).json()
    assert page1["total"] == 13 and len(page1["items"]) == 10
    page2 = client.get("/api/patients?limit=10&skip=10", headers=auth).json()
    assert len(page2["items"]) == 3

    assert client.get("/api/patients?q=unique", headers=auth).json()["total"] == 1  # case-insensitive
    assert client.get("/api/patients?q=fever", headers=auth).json()["total"] == 12
    assert client.get("/api/patients?q=zzzz", headers=auth).json()["total"] == 0


# ---------- dashboard ----------
def test_dashboard_stats(client, auth):
    empty = client.get("/api/dashboard/stats", headers=auth).json()
    assert empty["total_patients"] == 0 and empty["recent_patients"] == []

    client.post(
        "/api/patients",
        json={**FICTIONAL_PATIENT, "appointment_date": date.today().isoformat()},
        headers=auth,
    )
    client.post("/api/patients", json={"full_name": "AI Person", "age": 8, "source": "ai_extractor"}, headers=auth)

    stats = client.get("/api/dashboard/stats", headers=auth).json()
    assert stats["total_patients"] == 2
    assert stats["new_this_week"] == 2
    assert stats["appointments_today"] == 1
    assert stats["ai_extractions"] == 1
    assert stats["gender_distribution"]["Male"] == 1 and stats["gender_distribution"]["Other"] == 1
    buckets = {b["label"]: b["count"] for b in stats["age_distribution"]}
    assert buckets["36-50"] == 1 and buckets["0-17"] == 1
    assert len(stats["recent_activities"]) == 2
