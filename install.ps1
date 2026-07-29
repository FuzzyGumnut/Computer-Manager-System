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

# Check if Python is installed
Write-Host "Checking for Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python not found!" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://www.python.org/downloads/" -ForegroundColor Yellow
    Write-Host "During installation, make sure to check 'Add Python to PATH'" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    exit 1
}

# Check if pip is available
Write-Host "Checking for pip..." -ForegroundColor Yellow
try {
    $pipVersion = pip --version 2>&1
    Write-Host "pip found: $pipVersion" -ForegroundColor Green
} catch {
    Write-Host "pip not found!" -ForegroundColor Red
    Write-Host "Python installation appears to be incomplete." -ForegroundColor Yellow
    Write-Host "Please reinstall Python with pip included." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Press any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
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

# Download files from GitHub
Write-Host ""
Write-Host "Downloading files from GitHub..." -ForegroundColor Yellow
try {
    $clientUrl = "https://raw.githubusercontent.com/FuzzyGumnut/Computer-Manager-System/main/client.py"
    $requirementsUrl = "https://raw.githubusercontent.com/FuzzyGumnut/Computer-Manager-System/main/requirements.txt"
    
    Invoke-WebRequest -Uri $clientUrl -OutFile "$installDir\client.py" -UseBasicParsing
    Write-Host "Downloaded: client.py" -ForegroundColor Green
    
    Invoke-WebRequest -Uri $requirementsUrl -OutFile "$installDir\requirements.txt" -UseBasicParsing
    Write-Host "Downloaded: requirements.txt" -ForegroundColor Green
} catch {
    Write-Host "Error downloading files: $_" -ForegroundColor Red
    Write-Host "Please check your internet connection and try again." -ForegroundColor Yellow
    exit 1
}

# Install Python dependencies
Write-Host ""
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
try {
    & pip install -r "$installDir\requirements.txt" --quiet
    Write-Host "Dependencies installed successfully" -ForegroundColor Green
} catch {
    Write-Host "Error installing dependencies: $_" -ForegroundColor Red
    Write-Host "Some dependencies may have failed to install." -ForegroundColor Yellow
    Write-Host "The client may not function correctly." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Press any key to continue anyway or Ctrl+C to cancel..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
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
