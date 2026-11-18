@echo off
REM persona-bot — Windows double-click launcher (DoD 1)
setlocal EnableExtensions
cd /d "%~dp0"

where uv >nul 2>&1
if errorlevel 1 (
  echo Installing uv...
  powershell -NoProfile -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
  set "PATH=%USERPROFILE%\.local\bin;%USERPROFILE%\.cargo\bin;%PATH%"
)

if not exist ".env" (
  copy /Y ".env.example" ".env" >nul
  echo Created .env from .env.example — set GROQ_API_KEY and GROQ_MODEL_* in .env
)

if not exist "data" mkdir data

set STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
REM persona-bot CLI binds 127.0.0.1; see docs\FIRST_RUN.md for Streamlit email skip.
uv sync
if errorlevel 1 (
  echo uv sync failed
  pause
  exit /b 1
)

uv run persona-bot
if errorlevel 1 (
  echo persona-bot exited with an error
  pause
  exit /b 1
)

endlocal
