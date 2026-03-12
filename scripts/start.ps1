# ═══════════════════════════════════════════════════════════════
#  Autify Engine V1 — Windows PowerShell Deployment Script
#  Starts backend + dashboard without Docker.
#  Requires: Python 3.11+, Node.js 18+
#  Ports: BACKEND=18080 | DASHBOARD=18300 | LLM=18434
# ═══════════════════════════════════════════════════════════════

Write-Host ""
Write-Host "  ╔══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "  ║   Autify Engine V1 — Local Deployment    ║" -ForegroundColor Cyan
Write-Host "  ║   Zero-Cloud · Draft-Only · Secure       ║" -ForegroundColor Cyan
Write-Host "  ╚══════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Stop"
$RootDir = Split-Path -Parent $PSScriptRoot

# ── Configurable Ports ────────────────────────────────────
$BackendPort   = if ($env:BACKEND_PORT)   { $env:BACKEND_PORT }   else { "18080" }
$DashboardPort = if ($env:DASHBOARD_PORT) { $env:DASHBOARD_PORT } else { "18300" }

# ── Scan for Port Conflicts ──────────────────────────────
function Test-PortFree($port) {
    $conn = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
    if ($conn) {
        Write-Host "[WARNING] Port $port is already in use (PID $($conn[0].OwningProcess))." -ForegroundColor Yellow
        $override = Read-Host "  Override? Enter new port or press Enter to force"
        if ($override) { return $override }
    }
    return $port
}
$BackendPort   = Test-PortFree $BackendPort
$DashboardPort = Test-PortFree $DashboardPort

$env:BACKEND_PORT   = $BackendPort
$env:DASHBOARD_PORT = $DashboardPort

# ── Verify Prerequisites ─────────────────────────────────
try { python --version | Out-Null } catch {
    Write-Host "[ERROR] Python not found. Install Python 3.11+." -ForegroundColor Red
    exit 1
}
try { node --version | Out-Null } catch {
    Write-Host "[ERROR] Node.js not found. Install Node.js 18+." -ForegroundColor Red
    exit 1
}

# ── Ensure data directory ────────────────────────────────
New-Item -ItemType Directory -Force -Path "$RootDir\data" | Out-Null

# ── Install Python deps ──────────────────────────────────
Write-Host "[1/4] Installing Python dependencies..." -ForegroundColor Yellow
Push-Location $RootDir
pip install -r requirements.txt --quiet
Pop-Location

# ── Install Dashboard deps ───────────────────────────────
Write-Host "[2/4] Installing Dashboard dependencies..." -ForegroundColor Yellow
Push-Location "$RootDir\dashboard"
npm install --silent
Pop-Location

# ── Start Backend ────────────────────────────────────────
Write-Host "[3/4] Starting FastAPI backend on port $BackendPort..." -ForegroundColor Green
$backend = Start-Process -NoNewWindow -PassThru -FilePath "python" `
    -ArgumentList "-m uvicorn api.main:app --host 0.0.0.0 --port $BackendPort" `
    -WorkingDirectory $RootDir

# ── Start Dashboard ──────────────────────────────────────
Write-Host "[4/4] Starting React dashboard on port $DashboardPort..." -ForegroundColor Green
$dashboard = Start-Process -NoNewWindow -PassThru -FilePath "npm" `
    -ArgumentList "run dev" `
    -WorkingDirectory "$RootDir\dashboard"

Write-Host ""
Write-Host "  Backend:    http://localhost:$BackendPort"   -ForegroundColor White
Write-Host "  Dashboard:  http://localhost:$DashboardPort" -ForegroundColor White
Write-Host "  API Docs:   http://localhost:$BackendPort/docs" -ForegroundColor White
Write-Host ""
Write-Host "  Press Ctrl+C to stop all services." -ForegroundColor DarkGray

try {
    Wait-Process -Id $backend.Id
} finally {
    Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
    Stop-Process -Id $dashboard.Id -Force -ErrorAction SilentlyContinue
    Write-Host "  Services stopped." -ForegroundColor Yellow
}
