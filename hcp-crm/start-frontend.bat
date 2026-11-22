@echo off
REM Starts the HCP CRM frontend (React). Double-click or run from any folder.
cd /d "%~dp0frontend"
if not exist node_modules (
  echo Installing packages, this takes a few minutes the first time...
  call npm install
)
if not exist .env copy .env.example .env >nul
call npm start
pause
