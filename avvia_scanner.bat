@echo off
title Scanner Web Multi - Windows Web App
color 0B

echo ========================================================
echo          SCANNER WEB MULTI - WEB APP WINDOWS
echo ========================================================
echo.

:: Controlla se Python e installato
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERRORE] Python non e stato trovato nel sistema!
    echo Assicurati di installare Python da https://www.python.org/
    echo e di spuntare 'Add Python to PATH'.
    pause
    exit /b 1
)

echo [1/3] Verifica requisiti e dipendenze...
python -m pip install -r requirements.txt --quiet

echo [2/3] Verifica e liberazione porta 5000 da istanze precedenti...
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }" >nul 2>&1

echo [3/3] Avvio server locale e apertura browser...
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:5000"

echo [3/3] Applicazione avviata! Il browser si aprira automaticamente.
echo Premi CTRL+C nella finestra per arrestare il server.
echo.
python app.py
pause
