@echo off
REM Start the RQ worker for background job processing
REM Run this in a separate terminal window alongside the FastAPI server

cd /d "%~dp0"

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

echo Starting RQ worker on queue "voting_system"...
python worker.py
