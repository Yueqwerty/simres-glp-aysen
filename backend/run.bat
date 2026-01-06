@echo off
cd /d "%~dp0"
cd ..
set PYTHONPATH=%cd%
cd backend
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
