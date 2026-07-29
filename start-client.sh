#!/bin/bash
# Start the Computer Manager Client Agent

cd "$(dirname "$0")"

SERVER_HOST=${1:-localhost}
SERVER_PORT=${2:-8765}

echo "Starting Computer Manager Client Agent..."
echo "Connecting to: $SERVER_HOST:$SERVER_PORT"
python3 client.py "$SERVER_HOST" "$SERVER_PORT"
