#!/data/data/com.termux/files/usr/bin/bash
# Stop semua: server + watchdog + tunnel

echo ""
echo "🛑 Stopping all services..."
echo ""

# Stop watchdog
WATCHDOG_PID=$(cat "$HOME/capture-pro/watchdog.pid" 2>/dev/null)
if [ -n "$WATCHDOG_PID" ]; then
    echo "  Stopping watchdog (PID: $WATCHDOG_PID)..."
    kill "$WATCHDOG_PID" 2>/dev/null
    rm -f "$HOME/capture-pro/watchdog.pid"
fi

# Kill watchdog proses lain
pkill -f "watchdog.sh" 2>/dev/null

# Stop server
echo "  Stopping Flask server..."
PIDS=$(ps aux 2>/dev/null | grep "python run.py" | grep -v grep | awk '{print $2}')
if [ -n "$PIDS" ]; then
    for PID in $PIDS; do
        kill "$PID" 2>/dev/null
    done
    sleep 2
    
    # Force kill
    for PID in $PIDS; do
        kill -9 "$PID" 2>/dev/null
    done
fi

# Stop tunnel
echo "  Stopping tunnel..."
bash "$HOME/capture-pro/tunnel_service.sh" stop 2>/dev/null

# Release wake lock
if command -v termux-wake-unlock >/dev/null 2>&1; then
    termux-wake-unlock
fi

echo ""
echo "✅ All stopped"
echo ""
