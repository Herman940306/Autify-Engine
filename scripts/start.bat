@echo off
REM ═══════════════════════════════════════════════════════════
REM  Autify Engine V1 — Windows Deployment Script
REM  Starts backend + dashboard without Docker.
REM  Requires: Python 3.11+, Node.js 18+
REM  Ports: BACKEND=18080 | DASHBOARD=18300 | LLM=18434
REM ═══════════════════════════════════════════════════════════

echo.
echo  ╔══════════════════════════════════════════╗
echo  ║   Autify Engine V1 — Local Deployment    ║
echo  ║   Zero-Cloud · Draft-Only · Secure       ║
echo  ╚══════════════════════════════════════════╝
echo.

REM ── Configurable Ports ──────────────────────────────────
if "%BACKEND_PORT%"=="" set BACKEND_PORT=18080
if "%DASHBOARD_PORT%"=="" set DASHBOARD_PORT=18300

REM ── Check Python ────────────────────────────────────────
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.11+.
    pause
    exit /b 1
)

REM ── Check Node ──────────────────────────────────────────
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found. Please install Node.js 18+.
    pause
    exit /b 1
)

REM ── Ensure data directory ───────────────────────────────
if not exist data mkdir data

REM ── Install Python dependencies ─────────────────────────
echo [1/4] Installing Python dependencies...
pip install -r requirements.txt --quiet

REM ── Install Dashboard dependencies ─────────────────────
echo [2/4] Installing Dashboard dependencies...
cd dashboard
call npm install --silent
cd ..

REM ── Start Backend ──────────────────────────────────────
echo [3/4] Starting FastAPI backend on port %BACKEND_PORT%...
start /B cmd /c "python -m uvicorn api.main:app --host 0.0.0.0 --port %BACKEND_PORT%"

REM ── Start Dashboard ────────────────────────────────────
echo [4/4] Starting React dashboard on port %DASHBOARD_PORT%...
cd dashboard
start /B cmd /c "npm run dev"
cd ..

echo.
echo  Backend:    http://localhost:%BACKEND_PORT%
echo  Dashboard:  http://localhost:%DASHBOARD_PORT%
echo  API Docs:   http://localhost:%BACKEND_PORT%/docs
echo.
echo  Press any key to stop all services...
pause >nul

REM ── Cleanup ────────────────────────────────────────────
taskkill /F /IM uvicorn.exe >nul 2>&1
taskkill /F /IM node.exe >nul 2>&1
echo  Services stopped.
