@echo off
setlocal

cd /d "%~dp0"

set "QUICKSERVE_DIR=%PROGRAMDATA%\quickserve"
set "MODULE_DIR=%QUICKSERVE_DIR%\modules\sample_module"

echo "Creating virtual environment..."
py -m venv .venv
call .venv\Scripts\activate.bat
echo "Done!""

echo "Installing requirements..."
py -m pip install -e .
echo "Done!""

echo "Creating module directory..."
if not exist "%QUICKSERVE_DIR%\modules" mkdir "%QUICKSERVE_DIR%\modules"

if exist "%MODULE_DIR%" (
    echo "Removing existing sample_module..."
    rmdir /s /q "%MODULE_DIR%"
)

echo Linking sample_module...
mklink /J "%MODULE_DIR%" "%~dp0sample_module"

if errorlevel 1 (
    echo "Failed to create module symlink!"
    exit /b 1
)

echo "Create an admin account!"
py src\manager.py createadmin
echo "Done!"

echo "Start the server by executing run-windows.bat!"
