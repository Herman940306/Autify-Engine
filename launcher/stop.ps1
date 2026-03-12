# =================================================================
#  Autify Engine V1 - Stop All Services
# =================================================================

$BackendPort   = if ($env:BACKEND_PORT)   { $env:BACKEND_PORT }   else { "18080" }
$DashboardPort = if ($env:DASHBOARD_PORT) { $env:DASHBOARD_PORT } else { "18300" }

Write-Host ""
Write-Host "  Autify Engine V1 - Stopping services..." -ForegroundColor Yellow
Write-Host ""

$stopped = 0

foreach ($port in @($BackendPort, $DashboardPort)) {
    $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if ($conns) {
        foreach ($c in $conns) {
            $procId = $c.OwningProcess
            $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
            $name = if ($proc) { $proc.ProcessName } else { "unknown" }
            Write-Host "  Stopping $name (PID $procId) on port $port" -ForegroundColor Yellow
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
            $stopped++
        }
    }
}

if ($stopped -eq 0) {
    Write-Host "  No Autify Engine services found running." -ForegroundColor DarkGray
} else {
    Write-Host ""
    Write-Host "  Stopped $stopped process(es). All services shut down." -ForegroundColor Green
}
Write-Host ""
