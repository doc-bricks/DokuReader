@echo off
setlocal DisableDelayedExpansion
"%SystemRoot%\System32\wscript.exe" //I //Nologo "%~dp0launch.vbs"
exit /b %ERRORLEVEL%
