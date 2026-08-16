@echo off
title Voice Changer AI & Log Bot 24/7
cd /d "%~dp0"
echo ============================================================
echo      🎙 Voice Changer AI + 🕵️‍♂️ Spy Log Bot ishga tushmoqda...
echo ============================================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [!] Python virtual muhit topilmadi. O'rnatilmoqda...
    python -m venv .venv
    call .venv\Scripts\activate
    pip install -r requirements.txt
) else (
    call .venv\Scripts\activate
)

echo [*] Botlar ulanmoqda...
python -u bot.py

pause
