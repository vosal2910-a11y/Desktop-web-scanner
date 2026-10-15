@echo off
title Caricamento su GitHub - Scanner Web Multi
color 0A

echo ========================================================
echo       CARICAMENTO PROGETTO SU GITHUB (PUSH)
echo ========================================================
echo.
echo Repository di destinazione:
echo https://github.com/vosal2910-a11y/Desktop-web-scanner
echo.
echo [1/2] Verifica connessione a Git...
"C:\Users\s.bruno\AppData\Local\Programs\Git\cmd\git.exe" remote -v
echo.
echo [2/2] Invio dei file su GitHub (ramo main)...
echo --------------------------------------------------------
echo NOTA: Se si apre il browser o una finestra di GitHub,
echo clicca 'Sign in with your browser' per autorizzare
echo il caricamento.
echo --------------------------------------------------------
echo.
"C:\Users\s.bruno\AppData\Local\Programs\Git\cmd\git.exe" push -u origin main
echo.
if %errorlevel% equ 0 (
    echo ========================================================
    echo  SUCCESSO! Il progetto e stato caricato su GitHub:
    echo  https://github.com/vosal2910-a11y/Desktop-web-scanner
    echo ========================================================
) else (
    echo ========================================================
    echo  Attenzione: il caricamento non e andato a buon fine.
    echo  Verifica di essere loggato con l'account vosal2910-a11y.
    echo ========================================================
)
echo.
pause
