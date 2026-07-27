@echo off
cd /d %~dp0\..
if exist .venv\Scripts\python.exe (
    .venv\Scripts\python.exe sender_main.py
) else (
    echo Virtual environment not found.
    echo Create it first with: py -3.12 -m venv .venv
    exit /b 1
)