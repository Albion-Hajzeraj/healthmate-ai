@echo off
REM HealthMate AI - nisja me nje klik ne Windows
cd /d "%~dp0"
if not exist ".venv" (
    echo Po pergatitet ambienti per heren e pare...
    python -m venv .venv
    call .venv\Scripts\activate.bat
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate.bat
)
python run.py
pause
