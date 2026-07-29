#!/bin/bash

# Install Computer Manager Client as a launch agent to run on startup

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST_FILE="$SCRIPT_DIR/com.computer-manager.client.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
TARGET_PLIST="$LAUNCH_AGENTS_DIR/com.computer-manager.client.plist"

echo "Installing Computer Manager Client as launch agent..."

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$LAUNCH_AGENTS_DIR"

# Copy plist file
cp "$PLIST_FILE" "$TARGET_PLIST"

# Load the launch agent
launchctl unload "$TARGET_PLIST" 2>/dev/null
launchctl load "$TARGET_PLIST"

echo "Computer Manager Client installed as launch agent."
echo "It will now start automatically on login."
echo "To uninstall, run: ./uninstall-client-startup.sh"
echo ""
echo "To check status: launchctl list | grep computer-manager"
echo "To view logs: tail -f /tmp/computer-manager-client.log"
