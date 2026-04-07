@echo off
setlocal
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 "%~dp0\%~n0.py" %*
) else (
  python "%~dp0\%~n0.py" %*
)
endlocal
