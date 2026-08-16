@echo off
chcp 65001 > nul
title Telegram Voice Changer Bot

echo ======================================================
echo       🎙 TELEGRAM VOICE CHANGER BOT ISHGA TUSHMOQDA
echo ======================================================
echo.

cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [XATOLIK] Virtual muhit (.venv) topilmadi!
    pause
    exit /b
)

.venv\Scripts\python.exe bot.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [Dastur to'xtadi]
    pause
)
