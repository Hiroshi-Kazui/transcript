@echo off
setlocal
cd /d "%~dp0"

if "%~1"=="" (
    echo Usage: Drag ^& drop an audio folder onto this .bat file
    pause
    exit /b 1
)

".venv\Scripts\python.exe" -m transcript.cli "%~1"

echo.
echo Done.
pause
