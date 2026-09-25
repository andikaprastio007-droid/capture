#!/data/data/com.termux/files/usr/bin/bash
# Start semua: server + watchdog + tunnel + webhook

cd "$HOME/capture-pro" || exit 1

LOG="$HOME/capture-pro/server.log"

echo ""
echo "╔════════════════════════════════════════╗"
echo "║   ReconPro — Start All Services        ║"
echo "╚════════════════════════════════════════╝"
echo ""

# 1. Aktifkan wake lock (biar tidak mati saat HP lock)
if command -v termux-wake-lock >/dev/null 2>&1; then
    termux-wake-lock
    echo "✅ Wake lock aktif"
fi

# 2. Stop yang lama
echo "🛑 Stopping old processes..."
WATCHDOG_PID=$(cat watchdog.pid 2>/dev/null)
if [ -n "$WATCHDOG_PID" ]; then
    kill "$WATCHDOG_PID" 2>/dev/null
fi
pkill -f "python run.py" 2>/dev/null
pkill -f "watchdog.sh" 2>/dev/null
sleep 3

# 3. Start server
echo "🚀 Starting Flask server..."
if command -v setsid >/dev/null 2>&1; then
    setsid python run.py >> "$LOG" 2>&1 < /dev/null &
else
    nohup python run.py >> "$LOG" 2>&1 < /dev/null &
    disown 2>/dev/null
fi
sleep 6

# 4. Cek server
if ps aux 2>/dev/null | grep "python run.py" | grep -v grep > /dev/null 2>&1; then
    echo "✅ Server running on port 8000"
else
    echo "⚠️  Server tidak terdeteksi — cek log"
fi

# 5. Start tunnel
echo "🌐 Starting Cloudflare tunnel..."
bash tunnel_service.sh start >> "$LOG" 2>&1
sleep 12

TUNNEL_URL=$(bash tunnel_service.sh url 2>/dev/null)
if [ -n "$TUNNEL_URL" ]; then
    echo "✅ Tunnel: $TUNNEL_URL"
else
    echo "⚠️  Tunnel URL belum siap"
fi

# 6. Start watchdog
echo "👁️  Starting watchdog..."
nohup bash watchdog.sh > /dev/null 2>&1 &
disown 2>/dev/null
sleep 2

WATCHDOG_PID=$(cat watchdog.pid 2>/dev/null)
if [ -n "$WATCHDOG_PID" ]; then
    echo "✅ Watchdog running (PID: $WATCHDOG_PID)"
fi

# 7. Update webhook
if [ -n "$TUNNEL_URL" ]; then
    echo "📡 Updating webhook..."
    bash set-webhook.sh > /dev/null 2>&1
    echo "✅ Webhook updated"
fi

echo ""
echo "╔════════════════════════════════════════╗"
echo "║   ✅ SEMUA SERVICE AKTIF               ║"
echo "╚════════════════════════════════════════╝"
echo ""
echo "   🌐 Local:  http://localhost:8000"
if [ -n "$TUNNEL_URL" ]; then
    echo "   🌍 Public: $TUNNEL_URL"
fi
echo "   👁️  Watchdog: aktif (auto-restart)"
echo "   📱 Telegram bot: siap terima command"
echo ""
echo "   Cek status:  ~/capture-pro/status.sh"
echo "   Stop:        ~/capture-pro/stopall.sh"
echo ""
