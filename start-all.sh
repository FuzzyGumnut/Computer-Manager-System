#!/bin/bash
# Start Computer Manager Server and Web GUI

cd "$(dirname "$0")"

echo "🚀 Starting Computer Manager System..."
echo ""

# Start server in background
echo "📡 Starting server..."
python3 server.py > /tmp/computer-manager-server.log 2>&1 &
SERVER_PID=$!
echo "✓ Server started (PID: $SERVER_PID)"

# Wait for server to start
sleep 2

# Start web GUI
echo "🌐 Starting web GUI..."
cd web-gui
npm run dev > /tmp/computer-manager-gui.log 2>&1 &
GUI_PID=$!
echo "✓ Web GUI started (PID: $GUI_PID)"

cd ..

echo ""
echo "✅ Computer Manager is running!"
echo "   Server: http://localhost:8765"
echo "   Web GUI: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both services"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping services..."
    kill $SERVER_PID 2>/dev/null
    kill $GUI_PID 2>/dev/null
    echo "✓ Services stopped"
    exit 0
}

# Trap Ctrl+C
trap cleanup SIGINT SIGTERM

# Keep script running
wait
