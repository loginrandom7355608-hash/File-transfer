@echo off
cd /d %~dp0\..
if not exist .venv\Scripts\python.exe (
    echo Virtual environment not found.
    exit /b 1
)
.venv\Scripts\python.exe -m PyInstaller --clean sender.spec