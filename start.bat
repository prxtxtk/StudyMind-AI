@echo off
echo.
echo ============================================
echo    StudyMind AI - RAG Study Agent
echo ============================================
echo.

REM Check if Ollama is running
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Ollama is running
) else (
    echo [INFO] Starting Ollama server...
    start "" "C:\Users\%USERNAME%\AppData\Local\Programs\Ollama\ollama.exe" serve
    timeout /t 3 /nobreak >nul
)

echo [INFO] Launching StudyMind AI...
echo [INFO] Opening http://localhost:8501
echo.
streamlit run app.py --server.port=8501 --browser.gatherUsageStats=false --server.fileWatcherType=none

pause
