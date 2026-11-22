@echo off
REM Starts the HCP CRM backend (FastAPI). Double-click or run from any folder.
cd /d "%~dp0backend"
if not exist venv (
  echo Creating virtual environment...
  python -m venv venv
  call venv\Scripts\activate
  pip install -r requirements.txt
) else (
  call venv\Scripts\activate
)
if not exist .env (
  copy .env.example .env >nul
  echo.
  echo Created backend\.env from the example. Edit it now: set DATABASE_URL password/port and GROQ_API_KEY, then run this script again.
  notepad .env
  pause
  exit /b
)
uvicorn app.main:app --reload --port 8000
pause
