#!/bin/bash
# TailorCV Deployment Script - Generic Web Server Deployment
# Usage: ./deploy.sh [port] [server_ip]
#   Examples:
#     ./deploy.sh                          # Default: port 8000, auto-detect IP
#     ./deploy.sh 8080                     # Custom port 8080
#     ./deploy.sh 8000 10.197.36.30        # Specific IP and port

set -e

# Configuration
PORT=${1:-8000}
SERVER_IP=${2:-$(hostname -I | awk '{print $1}')}
LOGFILE="tailorcv.log"
SERVICE_NAME="tailorcv"

echo "================================================"
echo "TailorCV Generic Web Server Deployment"
echo "================================================"
echo "Target: http://${SERVER_IP}:${PORT}"
echo "================================================"

# Check environment
echo "[1/6] Checking environment..."

# Check if running as root (recommended for systemd)
if [ "$EUID" -eq 0 ]; then 
    echo "  ✓ Running as root"
else
    echo "  ⚠ Running as non-root user (some features may not work)"
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "  ✓ Python version: $PYTHON_VERSION"

# Install dependencies
echo "[2/6] Installing dependencies..."
pip3 install -q --upgrade pip 2>&1 | grep -v "WARNING.*root" || true
pip3 install -q -r requirements.txt 2>&1 | grep -v "WARNING.*root" || true
echo "  ✓ Dependencies installed"

# Kill existing processes on the port
echo "[3/6] Freeing port ${PORT}..."
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "  ⚠ Port ${PORT} is in use"
    PIDS=$(lsof -Pi :$PORT -sTCP:LISTEN -t)
    for PID in $PIDS; do
        echo "    Killing process $PID..."
        kill -9 $PID 2>/dev/null || true
    done
    sleep 2
    
    # Double check
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "  ✗ Failed to free port ${PORT}"
        exit 1
    fi
fi
echo "  ✓ Port ${PORT} is available"

# Check for API keys
echo "[4/6] Checking API keys..."
API_KEY_SET=false
if [ -n "$GOOGLE_API_KEY" ]; then
    echo "  ✓ GOOGLE_API_KEY is set"
    API_KEY_SET=true
fi
if [ -n "$OPENAI_API_KEY" ]; then
    echo "  ✓ OPENAI_API_KEY is set"
    API_KEY_SET=true
fi
if [ -n "$ANTHROPIC_API_KEY" ]; then
    echo "  ✓ ANTHROPIC_API_KEY is set"
    API_KEY_SET=true
fi

if [ "$API_KEY_SET" = false ]; then
    echo "  ⚠ No API keys found in environment"
    echo "    Users will need to provide their own API keys via the UI"
fi

# Determine deployment method
echo "[5/6] Starting TailorCV server..."

# Try systemd first (if running as root)
if [ "$EUID" -eq 0 ] && systemctl is-active --quiet $SERVICE_NAME 2>/dev/null; then
    echo "  Using systemd service..."
    systemctl restart $SERVICE_NAME
    sleep 3
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo "  ✓ Service started via systemd"
        DEPLOYMENT_METHOD="systemd"
    else
        echo "  ✗ Systemd service failed, falling back to manual start"
        DEPLOYMENT_METHOD="manual"
    fi
elif [ "$EUID" -eq 0 ] && [ -f "/etc/systemd/system/${SERVICE_NAME}.service" ]; then
    echo "  Enabling and starting systemd service..."
    systemctl enable $SERVICE_NAME 2>/dev/null || true
    systemctl start $SERVICE_NAME
    sleep 3
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo "  ✓ Service started via systemd"
        DEPLOYMENT_METHOD="systemd"
    else
        echo "  ✗ Systemd service failed, falling back to manual start"
        DEPLOYMENT_METHOD="manual"
    fi
else
    DEPLOYMENT_METHOD="manual"
fi

# Manual deployment if systemd not available or failed
if [ "$DEPLOYMENT_METHOD" = "manual" ]; then
    echo "  Using manual background process..."
    nohup python3 api.py > "$LOGFILE" 2>&1 &
    PID=$!
    echo "  Started with PID: $PID"
    sleep 3
    
    if ps -p $PID > /dev/null 2>&1; then
        echo "  ✓ Server started successfully"
    else
        echo "  ✗ Failed to start server"
        echo ""
        echo "Error logs:"
        tail -20 "$LOGFILE"
        exit 1
    fi
fi

# Verify server is responding
echo "[6/6] Verifying deployment..."
sleep 2

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:${PORT} 2>/dev/null || echo "000")

if [ "$HTTP_CODE" = "200" ]; then
    echo "  ✓ Server is responding (HTTP $HTTP_CODE)"
else
    echo "  ✗ Server not responding (HTTP $HTTP_CODE)"
    if [ "$DEPLOYMENT_METHOD" = "systemd" ]; then
        echo ""
        echo "Service logs:"
        journalctl -u $SERVICE_NAME -n 20 --no-pager
    else
        echo ""
        echo "Server logs:"
        tail -20 "$LOGFILE"
    fi
    exit 1
fi

echo ""
echo "================================================"
echo "✅ TailorCV Deployed Successfully!"
echo "================================================"
echo ""
echo "Access URLs:"
echo "  • Local:    http://localhost:${PORT}"
echo "  • Network:  http://${SERVER_IP}:${PORT}"
echo ""
echo "Deployment Info:"
if [ "$DEPLOYMENT_METHOD" = "systemd" ]; then
    echo "  • Method:   systemd service"
    echo "  • Service:  $SERVICE_NAME"
    echo ""
    echo "Management Commands:"
    echo "  • Status:   sudo systemctl status $SERVICE_NAME"
    echo "  • Restart:  sudo systemctl restart $SERVICE_NAME"
    echo "  • Stop:     sudo systemctl stop $SERVICE_NAME"
    echo "  • Logs:     sudo journalctl -u $SERVICE_NAME -f"
else
    echo "  • Method:   Background process"
    echo "  • PID:      $PID"
    echo "  • Logfile:  $LOGFILE"
    echo ""
    echo "Management Commands:"
    echo "  • Logs:     tail -f $LOGFILE"
    echo "  • Stop:     kill $PID"
    echo "  • Restart:  ./deploy.sh $PORT $SERVER_IP"
fi
echo ""
echo "================================================"
