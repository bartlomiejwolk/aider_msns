@echo off
:: Windows batch file wrapper for list-files.py
:: Usage: list-files [directory] [options]

:: Find Python (try common locations)
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found in PATH
    echo Please ensure Python is installed and in your system PATH
    exit /b 1
)

:: Run the Python script with all arguments
python "%~dp0list-files.py" %*

:: Preserve the exit code from Python
exit /b %errorlevel%
