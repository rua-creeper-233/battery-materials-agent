@echo off
chcp 65001 >nul
title Battery Evidence Lab - Share

cd /d "%~dp0"

echo =============================================
echo   Battery Evidence Lab - 一键共享启动
echo =============================================
echo.
echo 即将启动本地科研服务和 HTTPS 临时隧道。
echo 请保持本窗口开启；按 Ctrl+C 可结束共享。
echo.
echo 网页会自动打开。启动后请从本窗口复制：
echo   1. https://...trycloudflare.com 地址
echo   2. 黄色显示的本次临时访问密钥
echo 然后填入网页右上角“上传文献”。
echo =============================================
echo.

start "" "https://rua-creeper-233.github.io/battery-materials-agent/"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-share.ps1"

echo.
echo 共享服务已经停止。
pause
