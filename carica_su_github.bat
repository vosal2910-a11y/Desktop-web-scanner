@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Caricamento su GitHub - Scanner Web Multi
color 0A

echo ========================================================
echo       CARICAMENTO PROGETTO SU GITHUB (PUSH)
echo ========================================================
echo.
echo Repository di destinazione:
echo https://github.com/vosal2910-a11y/Desktop-web-scanner
echo.

where git >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERRORE] Git non è stato trovato nel PATH di sistema!
    pause
    exit /b 1
)

echo [1/3] Aggiunta modifiche e creazione commit di ottimizzazione...
git add .
git commit -m "Ottimizzazione estrema risorse per Render.com: algoritmo magic_color 23x piu veloce, streaming PDF O(1) memoria, pre-downscale e tuning Gunicorn"

echo.
echo [2/3] Invio dei file su GitHub (ramo main)...
echo --------------------------------------------------------
echo NOTA: Se si apre il browser o una finestra di GitHub,
echo clicca 'Sign in with your browser' per autorizzare
echo il caricamento.
echo --------------------------------------------------------
echo.
git push -u origin main
echo.
if %errorlevel% equ 0 (
    echo ========================================================
    echo  SUCCESSO! Il progetto e stato caricato su GitHub:
    echo  https://github.com/vosal2910-a11y/Desktop-web-scanner
    echo ========================================================
) else (
    echo ========================================================
    echo  Attenzione: il caricamento non e andato a buon fine.
    echo  Verifica le credenziali o la connessione di rete.
    echo ========================================================
)
echo.
pause
