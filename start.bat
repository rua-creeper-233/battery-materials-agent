@echo off
chcp 65001 >nul
title Battery Materials Research Agent

cd /d "%~dp0"

echo ==========================================
echo   Battery Materials Research Agent
echo ==========================================
echo.
echo Starting local research agent...
echo Web: http://127.0.0.1:8765
echo.
echo Press Ctrl+C to stop the service.
echo ==========================================
echo.

start "" /b cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:8765"

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1"

echo.
echo Service stopped.
pause