@echo off
cd /d "%~dp0"
py -3 app.py
if errorlevel 1 (
 echo Install 64-bit Python 3 with Tcl/Tk, or use the packaged Windows release.
 pause
)
