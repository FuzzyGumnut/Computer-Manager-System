#!/bin/bash
# Start Computer Manager GUI with built-in WebSocket server

cd "$(dirname "$0")"

echo "🚀 Starting Computer Manager GUI..."
echo ""

# Start Python GUI (has built-in server)
echo "🖥️  Starting GUI with built-in server..."
python3 server_gui.py &
GUI_PID=$!
echo "✓ GUI started (PID: $GUI_PID)"

echo ""
echo "✅ Computer Manager is running!"
echo "   Server: ws://localhost:8765"
echo "   GUI: Native Python window"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping GUI..."
    kill $GUI_PID 2>/dev/null
    echo "✓ GUI stopped"
    exit 0
}

# Trap Ctrl+C
trap cleanup SIGINT SIGTERM

# Keep script running
wait
