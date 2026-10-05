@echo off
cd /d "%~dp0"
echo ==============================================
echo   CampusNav - first-time setup and start
echo ==============================================
where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python 3.9+ from python.org and tick "Add to PATH".
  pause
  exit /b 1
)
if not exist .venv (
  echo Creating virtual environment...
  python -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install -q -r requirements.txt
start "" http://127.0.0.1:5000
python run.py
pause
