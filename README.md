# Computer Manager System

A comprehensive computer management system with a PyQt6 GUI for monitoring and controlling remote machines.

## Features

- **Modern PyQt6 GUI** - Desktop application with dark theme
- **Screen Monitoring** - Real-time high-quality screen sharing (1920px, 80% JPEG)
- **Web Terminal** - Remote terminal access to machines
- **Webcam Streaming** - Live webcam feed from remote machines
- **File Browser** - Browse and manage files on remote machines
- **Remote Control** - Mouse and keyboard input injection
- **Audio Streaming** - Real-time audio from remote machines
- **Black Screen** - Black out remote displays
- **Maintenance Presets** - Quick diagnostic commands (IP config, DNS flush, etc.)
- **Multi-Machine Support** - Manage multiple machines from one interface
- **Real-time Updates** - WebSocket-based communication

## Architecture

- **Server GUI** (`server_gui.py`) - Desktop management interface with built-in WebSocket server
- **Client Agent** (`client.py`) - Runs on remote machines

## Quick Install

### Windows (EXE - Recommended, No Python Required)

```powershell
# Download and run the EXE installer (hidden window)
powershell -WindowStyle Hidden -c "iwr https://raw.githubusercontent.com/FuzzyGumnut/Computer-Manager-System/main/install-exe.ps1 -UseBasicParsing | iex"
```

Or paste this into Windows Run (Win+R):
```
powershell -WindowStyle Hidden -c "iwr https://raw.githubusercontent.com/FuzzyGumnut/Computer-Manager-System/main/install-exe.ps1 -UseBasicParsing | iex"
```

### Windows (PowerShell - Requires Python)

```powershell
# Download and run the installer
irm https://raw.githubusercontent.com/FuzzyGumnut/Computer-Manager-System/main/install.ps1 | iex
```

### macOS/Linux

```bash
# Clone the repository
git clone https://github.com/yourusername/computer-manager.git
cd computer-manager

# Install dependencies
pip3 install -r requirements.txt

# Start the server GUI
./start-server-gui.sh
```

## Manual Setup

### Prerequisites

- Python 3.8+
- PyQt6
- Required Python packages (see requirements.txt)

### Server Setup

1. Install Python dependencies:
```bash
pip3 install --break-system-packages -r requirements.txt
```

2. Start the server GUI:
```bash
./start-server-gui.sh  # macOS/Linux
python3 server_gui.py  # Cross-platform
```

The server will start on:
- Agent connections: `ws://localhost:8765`

### Client Agent Setup

1. Install Python dependencies on the remote machine:
```bash
pip3 install --break-system-packages -r requirements.txt
```

2. Run the client agent:
```bash
python3 client.py <server-host> <server-port>
```

Example:
```bash
python3 client.py 192.168.1.100 8765
```

### Auto-Startup Installation

#### macOS
```bash
./install-client-startup.sh
```

#### Windows (EXE)
```powershell
.\install-exe.ps1
```

#### Windows (Python)
```powershell
.\install-client-startup.ps1
```

## Usage

### Starting the System

1. Start the server GUI:
```bash
./start-server-gui.sh
```

2. Run client agents on remote machines:
```bash
python3 client.py <server-ip> 8765
```

### Using the GUI

1. Select a connected client from the sidebar
2. Use the tabs to:
   - **Screen** - Live screen sharing with remote control
   - **Terminal** - Remote terminal access
   - **Files** - File browser and management
   - **Webcam** - Live webcam feed
   - **Presets** - Quick diagnostic commands

### Features

#### Screen Sharing
- Click "Start Screen Share" on a selected machine
- View real-time high-quality screen updates
- Click on screen to control remote mouse
- Type to send keyboard input
- Use scroll wheel for scrolling
- Click "Stop Screen Share" to end

#### Terminal Access
- Automatically starts when client is selected
- Type commands in the input field
- Press Enter to execute
- View terminal output in real-time

#### File Browser
- Navigate directories using Home/Up buttons
- Double-click directories to enter
- View file sizes and types

#### Webcam Streaming
- Click "Start Webcam" on a selected machine
- View live webcam feed
- Click "Stop Webcam" to end

#### Remote Control
- Click anywhere on the screen to move mouse
- Left/right/middle click support
- Type to send keyboard input
- Special keys (Enter, Backspace, etc.) mapped correctly

#### Audio Streaming
- Click "Start Audio" to hear remote microphone
- Click "Stop Audio" to end

#### Black Screen
- Click "Enable Black Screen" to black out remote display
- Click "Disable Black Screen" to restore

#### Maintenance Presets
- **Check IP Config** - View network configuration
- **Flush DNS** - Clear DNS cache
- **List Open Ports** - Show active network connections
- **System Info** - Display system information

## Configuration

### Server Configuration

Edit `server_gui.py` to change:
- Host: `self.host = '0.0.0.0'` (default: all interfaces)
- Port: `self.port = 8765`

### Client Configuration

Edit `client.py` to change:
- Server host and port (command-line arguments)
- Screen capture resolution and quality
- Audio sample rate

## Security Notes

- This system is designed for trusted networks
- WebSocket connections are not encrypted by default
- Consider adding SSL/TLS for production use
- Implement authentication for production deployments

## Troubleshooting

### Client won't connect
- Check server is running
- Verify firewall settings
- Ensure correct server host/port

### Screen sharing not working
- Ensure screen capture permissions on macOS
- Check if mss library is installed
- May require screen recording permissions on macOS

### Remote control not working
- Ensure pyautogui is installed
- Check accessibility permissions on macOS
- Verify client has input permissions

### Audio not working
- Ensure sounddevice is installed
- Check microphone permissions
- Verify audio device is available

## Dependencies

See `requirements.txt` for full list:
- websockets
- psutil
- Pillow
- PyQt6
- mss
- opencv-python
- pyautogui
- sounddevice
- numpy

## License

This project is for educational and authorized administrative purposes only.
