#!/bin/bash

# Uninstall Computer Manager Client launch agent

LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
TARGET_PLIST="$LAUNCH_AGENTS_DIR/com.computer-manager.client.plist"

echo "Uninstalling Computer Manager Client launch agent..."

# Unload the launch agent
launchctl unload "$TARGET_PLIST" 2>/dev/null

# Remove the plist file
rm -f "$TARGET_PLIST"

echo "Computer Manager Client launch agent uninstalled."
echo "It will no longer start automatically on login."
echo ""
echo "To reinstall, run: ./install-client-startup.sh"
