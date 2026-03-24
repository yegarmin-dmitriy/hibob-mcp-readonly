@echo off
echo ============================================
echo  HiBob MCP Extension - Prerequisites Setup
echo  for Windows
echo ============================================
echo.

:: Check if Python 3.10+ is installed
python --version 2>nul | findstr /R "3\.1[0-9] 3\.[2-9][0-9]" >nul 2>&1
if %errorlevel%==0 (
    echo [OK] Python 3.10+ is already installed
    python --version
) else (
    echo [!] Python 3.10+ is required but not found.
    echo.
    echo     Please install Python from https://www.python.org/downloads/
    echo     IMPORTANT: Check "Add Python to PATH" during installation!
    echo.
    echo     After installing Python, run this script again.
    echo.
    pause
    exit /b 1
)

echo.

:: Check if uv is installed
where uv >nul 2>&1
if %errorlevel%==0 (
    echo [OK] uv is already installed
    uv --version
) else (
    echo [..] Installing uv...
    powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    if %errorlevel%==0 (
        echo [OK] uv installed successfully
    ) else (
        echo [!] Failed to install uv. Try manually:
        echo     pip install uv
        pause
        exit /b 1
    )
)

echo.
echo ============================================
echo  All prerequisites are installed!
echo.
echo  Next steps:
echo  1. Double-click hibob-readonly.mcpb
echo  2. Enter the credentials when prompted
echo  3. Restart Claude Desktop
echo ============================================
echo.
pause
