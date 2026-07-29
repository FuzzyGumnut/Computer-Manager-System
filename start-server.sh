#!/bin/bash
# Start the Computer Manager Server

cd "$(dirname "$0")"

echo "Starting Computer Manager Server..."
python3 server.py
