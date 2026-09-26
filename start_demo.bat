@echo off
REM start_demo.bat - one-button launcher for the RAG project demo
REM Edit the CONFIG block below to match your actual paths/ports.

REM ---------- CONFIG (edit these) ----------
set PROJECT_DIR=C:\Users\Lenovo\Desktop\RAG project
set VENV_PATH=%PROJECT_DIR%\venv
set HOST=127.0.0.1
set PORT=8000
set APP_MODULE=app:app
set FRONTEND_URL=http://%HOST%:%PORT%
REM ------------------------------------------

echo ==^> Checking internet connection (required for fonts/markdown CDN in the UI)...
ping -n 1 8.8.8.8 >NUL 2>&1
if errorlevel 1 (
    echo     WARNING: No internet detected. Fonts and markdown rendering in the UI may not load.
)

echo ==^> Checking Ollama...
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I "ollama.exe" >NUL
if errorlevel 1 (
    echo     Ollama not running, starting it...
    start "" "ollama" serve
    timeout /t 3 /nobreak >NUL
) else (
    echo     Ollama already running.
)

echo ==^> Checking required models...
ollama list | findstr /C:"qwen3:1.7b" >NUL
if errorlevel 1 (
    echo     Pulling qwen3:1.7b...
    ollama pull qwen3:1.7b
)
ollama list | findstr /C:"nomic-embed-text" >NUL
if errorlevel 1 (
    echo     Pulling nomic-embed-text...
    ollama pull nomic-embed-text
)

echo ==^> Activating environment...
cd /d "%PROJECT_DIR%"
if exist "%VENV_PATH%\Scripts\activate.bat" (
    call "%VENV_PATH%\Scripts\activate.bat"
)

echo ==^> Starting FastAPI server...
REM --reload OFF for demos: avoids reload-triggered ChromaDB re-init issues
start "RAG Server" cmd /c "uvicorn %APP_MODULE% --host %HOST% --port %PORT% > server.log 2>&1"

echo ==^> Waiting for server to become healthy...
set /a COUNT=0
:waitloop
curl -s "http://%HOST%:%PORT%/docs" >NUL 2>&1
if errorlevel 1 (
    set /a COUNT+=1
    if %COUNT% GEQ 30 (
        echo     Server did not come up in time. Check server.log
        pause
        exit /b 1
    )
    timeout /t 1 /nobreak >NUL
    goto waitloop
)

echo     Server is up.
echo ==^> Opening browser...
start "" "%FRONTEND_URL%"

echo.
echo Demo is live at %FRONTEND_URL%
echo Server is running in a separate window titled "RAG Server".
echo Close that window (or press Ctrl+C in it) to stop the server.
echo.
pause
