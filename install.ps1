# Computer Manager Installer for Windows
# Run this script to install the Computer Manager client

Write-Host "Computer Manager Installer" -ForegroundColor Cyan
Write-Host "=========================" -ForegroundColor Cyan
Write-Host ""

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "This script requires administrator privileges." -ForegroundColor Red
    Write-Host "Please run PowerShell as Administrator and try again." -ForegroundColor Yellow
    exit 1
}

# Set installation directory
$installDir = "$env:USERPROFILE\computer-manager"
Write-Host "Installation directory: $installDir" -ForegroundColor Yellow

# Create installation directory if it doesn't exist
if (-not (Test-Path $installDir)) {
    New-Item -ItemType Directory -Path $installDir -Force | Out-Null
    Write-Host "Created installation directory" -ForegroundColor Green
}

# Download files (in production, this would download from GitHub)
# For now, we'll assume files are already in the current directory
$scriptDir = $PSScriptRoot
Write-Host "Copying files from: $scriptDir" -ForegroundColor Yellow

# Copy all necessary files
$filesToCopy = @(
    "client.py",
    "requirements.txt"
)

foreach ($file in $filesToCopy) {
    $sourceFile = Join-Path $scriptDir $file
    $destFile = Join-Path $installDir $file
    if (Test-Path $sourceFile) {
        Copy-Item $sourceFile $destFile -Force
        Write-Host "Copied: $file" -ForegroundColor Green
    } else {
        Write-Host "Warning: $file not found in source directory" -ForegroundColor Yellow
    }
}

# Install Python dependencies
Write-Host ""
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
try {
    & pip install -r "$installDir\requirements.txt" --quiet
    Write-Host "Dependencies installed successfully" -ForegroundColor Green
} catch {
    Write-Host "Error installing dependencies: $_" -ForegroundColor Red
    exit 1
}

# Create startup script
Write-Host ""
Write-Host "Creating startup script..." -ForegroundColor Yellow
$startupScript = @"
@echo off
cd /d "%installDir%"
pythonw client.py localhost 8765
"@
$startupScript | Out-File "$installDir\start-client-hidden.bat" -Encoding ASCII
Write-Host "Startup script created" -ForegroundColor Green

# Add to Windows startup (hidden)
Write-Host ""
Write-Host "Adding to Windows startup..." -ForegroundColor Yellow
$startupShortcut = "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\Computer Manager Client.lnk"
$wscript = New-Object -ComObject WScript.Shell
$shortcut = $wscript.CreateShortcut($startupShortcut)
$shortcut.TargetPath = "$installDir\start-client-hidden.bat"
$shortcut.WindowStyle = 7  # Minimized
$shortcut.Save()
Write-Host "Added to Windows startup (hidden)" -ForegroundColor Green

Write-Host ""
Write-Host "Installation completed successfully!" -ForegroundColor Green
Write-Host "The client will start automatically on Windows startup." -ForegroundColor Cyan
Write-Host "To uninstall, run: uninstall.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "To start the client manually: $installDir\start-client-hidden.bat" -ForegroundColor Cyan
