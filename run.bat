@echo off
rem Parakh (परख) AI - one-command launcher
cd /d "%~dp0backend"
if not exist .venv (
    echo [setup] creating virtual environment...
    python -m venv .venv
)
call .venv\Scripts\activate.bat
pip install -r requirements.txt -q
echo.
echo [test] running unit tests...
pytest -q
echo.
echo [serve] starting engine on http://localhost:8000
echo        simulator : http://localhost:8000/static/index.html
echo        dashboard : http://localhost:8000/static/dashboard.html
start "" http://localhost:8000/static/index.html
uvicorn app.main:app --reload --port 8000