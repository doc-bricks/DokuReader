@echo off
setlocal
cd /d "%~dp0"

if not defined DOKUREADER_BUILD_ROOT set "DOKUREADER_BUILD_ROOT=%LOCALAPPDATA%\DokuReader\build-cache"
set "BUILD_ROOT=%DOKUREADER_BUILD_ROOT%"
set "BUILD_DIR=%BUILD_ROOT%\build"
set "WORK_DIR=%BUILD_ROOT%\work"

if not exist "%BUILD_DIR%" mkdir "%BUILD_DIR%"
if not exist "%WORK_DIR%" mkdir "%WORK_DIR%"

python -m PyInstaller --noconfirm --clean --workpath "%WORK_DIR%" --distpath "%BUILD_DIR%" DokuReader.spec
if errorlevel 1 (
    echo [FEHLER] PyInstaller-Build fehlgeschlagen.
    exit /b 1
)

if not exist "dist" mkdir "dist"
copy /Y "%BUILD_DIR%\DokuReader.exe" "dist\DokuReader.exe" >nul
if errorlevel 1 (
    echo [FEHLER] EXE konnte nicht nach dist kopiert werden.
    exit /b 1
)

echo [OK] dist\DokuReader.exe wurde aktualisiert.
