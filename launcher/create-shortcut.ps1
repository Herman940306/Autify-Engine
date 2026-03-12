# =================================================================
#  Autify Engine V1 - Desktop Shortcut Creator
#  Creates a .lnk shortcut on the user's Desktop that launches
#  the Autify Engine standalone GUI launcher (.pyw application).
# =================================================================

$ErrorActionPreference = "Stop"
$RootDir     = Split-Path -Parent $PSScriptRoot
$GuiLauncher = Join-Path $PSScriptRoot "gui.pyw"
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "Autify Engine.lnk"
$IconPath     = Join-Path $RootDir "launcher\autify.ico"

# Locate pythonw.exe (runs .pyw without console window)
$PythonBase = "$env:LOCALAPPDATA\Programs\Python\Python311"
$PythonW    = Join-Path $PythonBase "pythonw.exe"
if (-not (Test-Path $PythonW)) {
    # Fallback: search PATH
    $PythonW = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source
    if (-not $PythonW) {
        $PythonW = (Get-Command python.exe -ErrorAction SilentlyContinue).Source
        if (-not $PythonW) {
            Write-Host "  [ERROR] Python not found. Install Python 3.11+ first." -ForegroundColor Red
            exit 1
        }
    }
}

Write-Host ""
Write-Host "  Creating desktop shortcut for Autify Engine V1..." -ForegroundColor Cyan

# ── Create the .lnk shortcut ─────────────────────────────
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)

# Launch the GUI application (pythonw = no console window)
$Shortcut.TargetPath       = $PythonW
$Shortcut.Arguments        = "`"$GuiLauncher`""
$Shortcut.WorkingDirectory = $RootDir
$Shortcut.Description      = "Launch Autify Engine V1 - Zero-Cloud AI Workflow Assistant"
$Shortcut.WindowStyle      = 1  # Normal

# Use custom icon if it exists, else use a recognizable system icon
if (Test-Path $IconPath) {
    $Shortcut.IconLocation = $IconPath
} else {
    $Shortcut.IconLocation = "%SystemRoot%\System32\shell32.dll,21"
}

$Shortcut.Save()

Write-Host "  [OK] Shortcut created: $ShortcutPath" -ForegroundColor Green
Write-Host "       Target: $PythonW `"$GuiLauncher`"" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Double-click 'Autify Engine' on your Desktop to launch the GUI." -ForegroundColor White
Write-Host ""
