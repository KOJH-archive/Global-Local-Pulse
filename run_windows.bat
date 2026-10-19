@echo off
cd /d "%~dp0"
if not exist .env copy /Y .env.example .env >nul
if not exist .venv\Scripts\python.exe py -3.12 -m venv .venv
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m streamlit run app.py
pause
exit /b
:fail
echo Setup failed. Please install Python 3.12 and try again.
pause
exit /b 1
