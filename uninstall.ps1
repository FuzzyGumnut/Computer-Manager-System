# Computer Manager Uninstaller for Windows
# Run this script to remove the Computer Manager client

Write-Host "Computer Manager Uninstaller" -ForegroundColor Cyan
Write-Host "===========================" -ForegroundColor Cyan
Write-Host ""

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "This script requires administrator privileges." -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
    exit 1
}

# Remove from Windows startup
Write-Host "Removing from Windows startup..." -ForegroundColor Yellow
$startupShortcut = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\Computer Manager Client.lnk"
if (Test-Path $startupShortcut) {
    Remove-Item $startupShortcut -Force
    Write-Host "Removed from Windows startup" -ForegroundColor Green
} else {
    Write-Host "Startup shortcut not found" -ForegroundColor Yellow
}

# Stop any running client processes
Write-Host "Stopping any running client processes..." -ForegroundColor Yellow
try {
    Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object {
        $_.MainWindowTitle -like "*client*" -or $_.CommandLine -like "*client.py*"
    } | Stop-Process -Force
    Write-Host "Client processes stopped" -ForegroundColor Green
} catch {
    Write-Host "No client processes found or error stopping processes" -ForegroundColor Yellow
}

# Remove installation directory
$installDir = "$env:USERPROFILE\computer-manager"
Write-Host "Removing installation directory: $installDir" -ForegroundColor Yellow
if (Test-Path $installDir) {
    Remove-Item $installDir -Recurse -Force
    Write-Host "Installation directory removed" -ForegroundColor Green
} else {
    Write-Host "Installation directory not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Uninstallation completed successfully!" -ForegroundColor Green
Write-Host "The Computer Manager client has been removed from your system." -ForegroundColor Cyan
