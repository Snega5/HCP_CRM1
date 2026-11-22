# HCP CRM – Healthcare Customer Relationship Management System

A full-stack hospital CRM where staff manage patient records and use an LLM (Groq) to turn unstructured
medical notes into structured, reviewable patient data.

> **Fictional data only.** This is a portfolio/demo project and is not intended for real patient information.

| Layer | Technology |
|---|---|
| Frontend | React 18, JavaScript, HTML5, CSS3, Axios, React Router 6 |
| Backend | Python 3.10+, FastAPI, Pydantic v2, REST APIs, JWT auth |
| Database | PostgreSQL, SQLAlchemy 2 |
| AI | Groq API (`llama-3.3-70b-versatile`), JSON-mode extraction with server-side validation |

## Features

- **Authentication**: login page, JWT sessions, protected routes, logout, automatic sign-out on expired token
- **Dashboard**: total patients, new this week, appointments today, AI extractions, recent patients, recent activity, gender and age charts
- **Patient management**: add, view, search, edit and delete patients (paginated table, confirm-before-delete)
- **AI Patient Data Extractor**: paste free text, get a structured form, review/edit, then save
  - missing fields are returned as `null`, never invented
  - the backend re-validates the AI's JSON and drops any name, phone or email that does not appear in the source text
  - results are **never auto-saved**; the user must click *Save patient*
  - clear errors for a missing key, rate limit, timeout or invalid AI response
- **Relational database**: `users` → `patients` (created_by) and `activity_logs` (user_id, patient_id) with foreign keys
- **Tests**: pytest suite for auth, CRUD, search, dashboard and AI validation (runs on in-memory SQLite, Groq mocked)

## Project structure

```
hcp-crm/
  start-backend.bat        one-click backend start (Windows)
  start-frontend.bat       one-click frontend start (Windows)
  frontend/
    public/index.html
    src/
      components/   Layout, Sidebar, Topbar, StatCard, BarChart, Loader, Modal,
                    ConfirmDialog, PatientForm, PatientDetailModal, ProtectedRoute
      context/      AuthContext, NotificationContext (toasts)
      pages/        Login, Dashboard, Patients, AIExtractor
      services/     api.js (Axios + JWT interceptor), authService, dashboardService,
                    patientService, extractorService
      assets/
      App.js  index.js  index.css
    package.json  .env.example
  backend/
    app/
      routes/       auth.py  dashboard.py  patients.py  extract.py
      models/       user.py  patient.py  activity.py
      schemas/      auth.py  dashboard.py  patient.py  extraction.py
      services/     security.py (JWT/bcrypt)  groq_service.py  seed.py
      config.py  database.py  main.py
    tests/          conftest.py  test_api.py  test_extraction.py
    requirements.txt  requirements-dev.txt  pytest.ini  .env.example
  README.md
```

## Setup on Windows

### Prerequisites
- Node.js 18+ (https://nodejs.org)
- Python 3.10+ (tick "Add Python to PATH" in the installer)
- PostgreSQL 14+ (https://www.postgresql.org/download/windows/)
- A free Groq API key: https://console.groq.com/keys

### 1. Create the database
In pgAdmin (or the *SQL Shell (psql)* from the Start menu):

```sql
CREATE DATABASE hcp_crm;
```

Check which port PostgreSQL uses (default 5432, but some installs use 5433):

```powershell
netstat -ano | findstr LISTEN | findstr 543
```

### 2. Backend

```powershell
cd hcp-crm\backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
notepad .env
```

Edit `.env`:

```
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/hcp_crm   # use your real password and port
GROQ_API_KEY=gsk_your_key_here
SECRET_KEY=any-long-random-string
```

Special characters in the password must be URL-encoded (`@` becomes `%40`).

Start the API:

```powershell
uvicorn app.main:app --reload --port 8000
```

Tables are created automatically and one fictional dev user is seeded. Restart uvicorn after changing `.env`.

- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/api/health

### 3. Frontend (second terminal)

```powershell
cd hcp-crm\frontend
copy .env.example .env
npm install
npm start
```

Open http://localhost:3000 and sign in:

- **Username:** `admin`
- **Password:** `admin123`

(Change them with `SEED_ADMIN_USERNAME` / `SEED_ADMIN_PASSWORD` in `backend\.env` **before** the first run.)

**Shortcut:** after the first-time `.env` setup, double-click `start-backend.bat` and `start-frontend.bat`.

## How to use

1. **Patients → + Add patient**: fill the form (only the name is required). Use the row buttons to View, Edit or Delete. Search filters as you type.
2. **AI Extractor**: paste text such as
   `Patient John, 45 years old, male, visited the hospital with fever and headache. Diagnosed with viral fever. Assigned to Dr. Kumar.`
   and click **Extract Information**. You get:
   ```json
   {
     "patient_name": "John", "age": 45, "gender": "Male",
     "symptoms": "Fever and headache", "diagnosis": "Viral fever",
     "doctor_assigned": "Dr. Kumar", "phone": null, "email": null,
     "medical_history": null, "appointment_date": null
   }
   ```
   Review and edit the form, then click **Save patient**.
3. **Dashboard** updates automatically with totals, charts and activity.

## API reference

All routes except login and health require `Authorization: Bearer <token>`.

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/auth/login` | `{username, password}` returns token and user |
| GET | `/api/auth/me` | current user |
| GET | `/api/dashboard/stats` | dashboard numbers, charts, recent items |
| GET | `/api/patients?q=&skip=&limit=` | list and search, returns `{items, total}` |
| GET | `/api/patients/{id}` | one patient |
| POST | `/api/patients` | create (`source`: `manual` or `ai_extractor`) |
| PUT | `/api/patients/{id}` | partial update |
| DELETE | `/api/patients/{id}` | delete |
| POST | `/api/extract` | `{text}` returns extracted fields; **saves nothing** |
| GET | `/api/health` | liveness check |

## Testing

Automated (no PostgreSQL or Groq key needed; uses SQLite in memory and a mocked Groq call):

```powershell
cd hcp-crm\backend
venv\Scripts\activate
pip install -r requirements-dev.txt
pytest -v
```

Manual checklist:
- [ ] `/api/health` returns `{"status":"ok"}`
- [ ] Wrong password shows an error toast; correct login lands on the dashboard
- [ ] Opening `/patients` while logged out redirects to `/login`
- [ ] Add, edit, view and delete a patient; the dashboard numbers change
- [ ] Search by name, doctor and diagnosis
- [ ] AI Extractor: sample text fills six fields, others stay blank; nothing appears in Patients until you click Save
- [ ] Remove the Groq key and restart: the extractor shows a clear "key not configured" message

## Troubleshooting

| Problem | Fix |
|---|---|
| `Connection refused` on port 5432 | PostgreSQL is not running or uses another port (often 5433). Check with `netstat`, update `DATABASE_URL`. |
| Error still shows the old port | `.env` is missing, misnamed (`.env.txt`) or in the wrong folder. It must be `backend\.env`. |
| `password authentication failed` | Wrong password in `DATABASE_URL`. |
| `database "hcp_crm" does not exist` | Run `CREATE DATABASE hcp_crm;`. |
| Login says "Cannot reach the server" | Backend is not running on port 8000. |
| Extractor: "Groq API key is not configured" | Set `GROQ_API_KEY` in `backend\.env` and **restart** uvicorn. |
| Extractor: "rate limit" | Wait a minute and retry (free tier limits). |
| Changed `SEED_ADMIN_*` but login unchanged | Seeding only runs when the users table is empty. |

## Security notes

- API keys live only in `backend\.env` (git-ignored); the frontend never sees the Groq key.
- Passwords are bcrypt-hashed; sessions use signed JWTs that expire (default 8 hours).
- Set a long random `SECRET_KEY` and change the seeded password before any shared use.
- Tables are created with `create_all` for simplicity; a production system would use Alembic migrations, role-based permissions, audit retention and HIPAA/GDPR-grade controls.

## Possible next steps

Role-based access, user management, appointment calendar, file uploads, Alembic migrations, Docker Compose, CI pipeline.
