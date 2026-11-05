@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Scanner Web Multi - Suite di Test Automatizzati
color 0A

echo ========================================================
echo       ESECUZIONE TEST AUTOMATIZZATI SCANNER WEB MULTI
echo ========================================================
echo.

python -m unittest discover -s tests
echo.
echo ========================================================
echo Test completati.
echo ========================================================
pause
