# =================================================================
#  Autify Engine V1 - Desktop Launcher
#  Starts backend + dashboard, then opens app-mode browser window.
#  Supports: Chrome, Edge, or default browser fallback.
#  Handles restart: kills stale processes before relaunching.
# =================================================================

param(
    [switch]$NoBrowser,
    [switch]$Restart
)

$ErrorActionPreference = "Continue"
$RootDir = Split-Path -Parent $PSScriptRoot

# -- Branding ---------------------------------------------------
Write-Host ""
Write-Host "  ================================================" -ForegroundColor Cyan
Write-Host "       Autify Engine V1 - Desktop Launcher"          -ForegroundColor Cyan
Write-Host "       Zero-Cloud | Draft-Only | Secure"             -ForegroundColor Cyan
Write-Host "  ================================================" -ForegroundColor Cyan
Write-Host ""

# -- Ports ------------------------------------------------------
$BackendPort   = if ($env:BACKEND_PORT)   { $env:BACKEND_PORT }   else { "18080" }
$DashboardPort = if ($env:DASHBOARD_PORT) { $env:DASHBOARD_PORT } else { "18300" }

# -- PATH resolution (ensure Python + Node are found) -----------
$PythonBase = "$env:LOCALAPPDATA\Programs\Python\Python311"
$NodeBase   = "$env:ProgramFiles\nodejs"

foreach ($p in @($PythonBase, "$PythonBase\Scripts", $NodeBase)) {
    if ((Test-Path $p) -and ($env:Path -notlike "*$p*")) {
        $env:Path = "$p;$env:Path"
    }
}

# -- Prerequisite check -----------------------------------------
function Assert-Command($cmd, $label) {
    try { & $cmd --version 2>$null | Out-Null; return $true }
    catch {
        Write-Host "  [ERROR] $label not found in PATH." -ForegroundColor Red
        return $false
    }
}

$ok = (Assert-Command "python" "Python 3.11+") -and (Assert-Command "node" "Node.js 18+")
if (-not $ok) {
    Write-Host "  Install missing prerequisites and try again." -ForegroundColor Red
    Read-Host "  Press Enter to exit"
    exit 1
}

# -- Stop stale processes if restarting -------------------------
function Stop-ServiceOnPort($port, $label) {
    $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($conns) {
        foreach ($c in $conns) {
            $procId = $c.OwningProcess
            Write-Host "  [RESTART] Stopping stale $label (PID $procId) on port $port..." -ForegroundColor Yellow
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Seconds 1
    }
}

if ($Restart) {
    Stop-ServiceOnPort $BackendPort "Backend"
    Stop-ServiceOnPort $DashboardPort "Dashboard"
}

# -- Check if services already running --------------------------
function Test-ServiceRunning($port) {
    $conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    return ($null -ne $conn)
}

$backendRunning   = Test-ServiceRunning $BackendPort
$dashboardRunning = Test-ServiceRunning $DashboardPort

# -- Ensure data directory --------------------------------------
New-Item -ItemType Directory -Force -Path "$RootDir\data" | Out-Null

# -- Start Backend ----------------------------------------------
if (-not $backendRunning) {
    Write-Host "  [1/3] Starting FastAPI backend on port $BackendPort..." -ForegroundColor Green
    $env:BACKEND_PORT   = $BackendPort
    $env:DASHBOARD_PORT = $DashboardPort
    $backendProc = Start-Process -PassThru -WindowStyle Hidden -FilePath "python" `
        -ArgumentList "-m uvicorn api.main:app --host 127.0.0.1 --port $BackendPort" `
        -WorkingDirectory $RootDir

    # Wait for backend to become ready (max 15s)
    $waited = 0
    while ($waited -lt 15) {
        Start-Sleep -Seconds 1
        $waited++
        try {
            $null = Invoke-RestMethod "http://127.0.0.1:$BackendPort/health" -TimeoutSec 2
            Write-Host "  [OK] Backend ready (${waited}s)" -ForegroundColor Green
            break
        } catch { }
    }
    if ($waited -ge 15) {
        Write-Host "  [WARN] Backend may still be starting..." -ForegroundColor Yellow
    }
} else {
    Write-Host "  [1/3] Backend already running on port $BackendPort" -ForegroundColor DarkGreen
}

# -- Start Dashboard --------------------------------------------
if (-not $dashboardRunning) {
    Write-Host "  [2/3] Starting React dashboard on port $DashboardPort..." -ForegroundColor Green
    $env:BACKEND_PORT   = $BackendPort
    $env:DASHBOARD_PORT = $DashboardPort
    $dashboardProc = Start-Process -PassThru -WindowStyle Hidden -FilePath "cmd" `
        -ArgumentList "/c npm run dev" `
        -WorkingDirectory "$RootDir\dashboard"

    # Wait for dashboard to become ready (max 20s)
    $waited = 0
    while ($waited -lt 20) {
        Start-Sleep -Seconds 1
        $waited++
        try {
            $null = Invoke-WebRequest "http://127.0.0.1:$DashboardPort/" -UseBasicParsing -TimeoutSec 2
            Write-Host "  [OK] Dashboard ready (${waited}s)" -ForegroundColor Green
            break
        } catch { }
    }
    if ($waited -ge 20) {
        Write-Host "  [WARN] Dashboard may still be starting..." -ForegroundColor Yellow
    }
} else {
    Write-Host "  [2/3] Dashboard already running on port $DashboardPort" -ForegroundColor DarkGreen
}

# -- Launch browser in app/kiosk mode --------------------------
$DashUrl = "http://localhost:$DashboardPort"

if (-not $NoBrowser) {
    Write-Host "  [3/3] Launching Autify Engine desktop window..." -ForegroundColor Green

    # Prefer Edge (ships with Windows), then Chrome, then default browser
    $edgePath   = "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe"
    $edgeX86    = "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"
    $chromePath  = "$env:ProgramFiles\Google\Chrome\Application\chrome.exe"
    $chromeX86   = "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe"

    $appArgs = "--app=$DashUrl --window-size=1400,900 --disable-infobars --no-first-run"

    $browser = $null
    foreach ($bpath in @($edgePath, $edgeX86, $chromePath, $chromeX86)) {
        if (Test-Path $bpath) { $browser = $bpath; break }
    }

    if ($browser) {
        $browserName = if ($browser -like "*edge*") { "Edge" } else { "Chrome" }
        Write-Host "  Using $browserName app mode (no URL bar)" -ForegroundColor DarkGray
        Start-Process -FilePath $browser -ArgumentList $appArgs
    } else {
        Write-Host "  Opening in default browser..." -ForegroundColor DarkGray
        Start-Process $DashUrl
    }
} else {
    Write-Host "  [3/3] Skipped browser launch (-NoBrowser flag)" -ForegroundColor DarkGray
}

# -- Summary ----------------------------------------------------
Write-Host ""
Write-Host "  ------------------------------------------------" -ForegroundColor White
Write-Host "   Backend:   http://127.0.0.1:$BackendPort"         -ForegroundColor White
Write-Host "   Dashboard: http://localhost:$DashboardPort"        -ForegroundColor White
Write-Host "   API Docs:  http://127.0.0.1:$BackendPort/docs"    -ForegroundColor White
Write-Host "   Login:     admin / admin123 (change on first use)" -ForegroundColor White
Write-Host "  ------------------------------------------------" -ForegroundColor White
Write-Host ""
Write-Host "  Services are running in the background." -ForegroundColor DarkGray
Write-Host "  Run launcher\stop.ps1 to shut down." -ForegroundColor DarkGray
Write-Host ""
