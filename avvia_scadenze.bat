@echo off
REM Avvia l'applicazione Gestione Scadenze

echo ========================================
echo   Gestione Scadenze Veicoli e Personali
echo ========================================
echo.

REM Controlla se Python è installato
python --version >nul 2>&1
if errorlevel 1 (
    echo ERRORE: Python non trovato!
    echo Installa Python da https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

REM Vai alla directory del progetto
cd /d "%~dp0"

REM Controlla se esiste l'ambiente virtuale
if exist "venv\Scripts\activate.bat" (
    echo Attivazione ambiente virtuale...
    call venv\Scripts\activate.bat
) else (
    echo Ambiente virtuale non trovato.
    echo Eseguo con Python di sistema...
)

REM Controlla se plyer è installato
python -c "import plyer" >nul 2>&1
if errorlevel 1 (
    echo.
    echo Installazione dipendenze mancanti...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo ERRORE: Impossibile installare le dipendenze!
        pause
        exit /b 1
    )
)

REM Avvia l'applicazione
echo.
echo Avvio applicazione...
echo.
python main.py

REM Se l'applicazione termina con errore, mostra il messaggio
if errorlevel 1 (
    echo.
    echo L'applicazione si e' chiusa con errori.
    pause
)
