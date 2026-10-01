@echo off
setlocal DisableDelayedExpansion
chcp 65001 >nul
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_source.ps1" -Debug
set "DOKUREADER_EXIT=%ERRORLEVEL%"
pause
exit /b %DOKUREADER_EXIT%
