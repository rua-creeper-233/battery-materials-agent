@echo off
chcp 65001 >nul
title Battery Evidence Lab - Evidence RAG
cd /d "%~dp0"

start "" /b cmd /c "timeout /t 3 /nobreak >nul && start http://127.0.0.1:8765"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-rag.ps1"

echo.
echo RAG service stopped. The API key was not saved.
pause
