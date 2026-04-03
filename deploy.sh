#!/bin/bash
# TailorCV Deployment Script
# Usage: ./deploy.sh [port]

set -e

PORT=${1:-8000}
LOGFILE="tailorcv.log"

echo "================================================"
echo "TailorCV Deployment Script"
echo "================================================"

# Check if running on the target server
echo "Checking environment..."

# Install dependencies
echo "Installing dependencies..."
pip3 install -q -r requirements.txt
pip3 install -q fastapi uvicorn python-multipart pymupdf

# Check if port is available
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "WARNING: Port $PORT is already in use."
    echo "Kill existing process? (y/n)"
    read -r answer
    if [ "$answer" = "y" ]; then
        pkill -f "python3 api.py" || true
        sleep 2
    else
        echo "Deployment cancelled."
        exit 1
    fi
fi

# Check for API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo "WARNING: OPENAI_API_KEY environment variable not set."
    echo "Set it now? (y/n)"
    read -r answer
    if [ "$answer" = "y" ]; then
        echo "Enter your API key:"
        read -r apikey
        export OPENAI_API_KEY="$apikey"
    fi
fi

# Update port in api.py if different from 8000
if [ "$PORT" != "8000" ]; then
    echo "Updating port to $PORT..."
    sed -i "s/port=8000/port=$PORT/" api.py
fi

echo ""
echo "Starting TailorCV server on port $PORT..."
echo "Logs will be written to $LOGFILE"
echo ""

# Start server in background
nohup python3 api.py > "$LOGFILE" 2>&1 &
PID=$!

sleep 3

# Check if server started
if ps -p $PID > /dev/null; then
    echo "✅ TailorCV server started successfully!"
    echo "   PID: $PID"
    echo "   Port: $PORT"
    echo "   URL: http://$(hostname -I | awk '{print $1}'):$PORT"
    echo ""
    echo "To view logs:"
    echo "   tail -f $LOGFILE"
    echo ""
    echo "To stop the server:"
    echo "   kill $PID"
    echo "   OR: pkill -f 'python3 api.py'"
else
    echo "❌ Failed to start server. Check $LOGFILE for errors."
    cat "$LOGFILE"
    exit 1
fi

echo "================================================"
