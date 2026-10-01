@echo off
setlocal DisableDelayedExpansion
"%SystemRoot%\System32\wscript.exe" //B //Nologo "%~dp0launch.vbs"
exit /b %ERRORLEVEL%
