@echo off

rem Define the path to the virtual environment activation script
set VENV_ACTIVATE=.\venv\Scripts\activate.bat

echo Starting Celery worker...
rem The '/k' flag keeps the window open. We chain commands with '&&'.
rem First, activate the venv, then run the celery command.
rem **CRUCIAL FIX: Added --pool=solo for Windows compatibility**
start "Celery Worker" cmd /k "%VENV_ACTIVATE% && celery -A app.workers.tasks worker --loglevel=info --pool=solo"

echo Starting FastAPI server...
rem First, activate the venv, then run the uvicorn command.
rem **FIX: Using python -m uvicorn for better module resolution**
start "Uvicorn Server" cmd /k "%VENV_ACTIVATE% && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

echo.
echo Both services are starting in new windows.
echo To stop the services, close both new command prompt windows.