#!/data/data/com.termux/files/usr/bin/bash
# Restart server Flask — robust version

PROJECT="$HOME/capture-pro"
LOG_FILE="$PROJECT/server.log"

cd "$PROJECT" || exit 1

{
    echo ""
    echo "======================================"
    echo "[restart] $(date) — via Telegram/Editor"
    echo "======================================"
} >> "$LOG_FILE" 2>&1

echo "[restart] Killing old server..." >> "$LOG_FILE"

# ==== KILL dengan berbagai cara ====
# 1. Cari PID manual
PIDS=$(ps aux | grep "python run.py" | grep -v grep | awk '{print $2}')

if [ -n "$PIDS" ]; then
    echo "[restart] Found PIDs: $PIDS" >> "$LOG_FILE"
    for PID in $PIDS; do
        echo "[restart] Killing PID: $PID" >> "$LOG_FILE"
        kill "$PID" 2>/dev/null
    done
    sleep 3
    
    # Force kill kalau bandel
    for PID in $PIDS; do
        kill -9 "$PID" 2>/dev/null
    done
    sleep 2
else
    echo "[restart] No old process found" >> "$LOG_FILE"
fi

# 2. Fallback pkill
pkill -f "python run.py" 2>/dev/null
sleep 1

echo "[restart] Starting new server..." >> "$LOG_FILE"

# ==== START baru — DETACHED ====
cd "$PROJECT"

# Pakai setsid kalau ada, atau nohup
if command -v setsid >/dev/null 2>&1; then
    setsid python run.py >> "$LOG_FILE" 2>&1 < /dev/null &
else
    nohup python run.py >> "$LOG_FILE" 2>&1 < /dev/null &
    disown 2>/dev/null
fi

NEW_PID=$!
echo "[restart] New PID (bg): $NEW_PID" >> "$LOG_FILE"

# Tunggu server start
sleep 5

# Cek server hidup
if netstat -tulpn 2>/dev/null | grep -q ":8000 "; then
    echo "[restart] ✅ Server running on port 8000" >> "$LOG_FILE"
else
    echo "[restart] ⚠️  Port 8000 tidak aktif — cek log" >> "$LOG_FILE"
fi

# Auto-set webhook kalau tunnel jalan
sleep 3
TUNNEL_URL=$(bash "$PROJECT/tunnel_service.sh" url 2>/dev/null)
if [ -n "$TUNNEL_URL" ] && [ "$TUNNEL_URL" != "STOPPED" ]; then
    if [ -f "$PROJECT/.env" ]; then
        export $(grep -v '^#' "$PROJECT/.env" | grep -E '^TG_TOKEN=' | xargs)
        if [ -n "$TG_TOKEN" ]; then
            curl -s -X POST "https://api.telegram.org/bot${TG_TOKEN}/setWebhook" \
                -H "Content-Type: application/json" \
                -d "{\"url\":\"${TUNNEL_URL}/tg/webhook\"}" >> "$LOG_FILE" 2>&1
            echo "[restart] Webhook re-set to: ${TUNNEL_URL}/tg/webhook" >> "$LOG_FILE"
        fi
    fi
fi

echo "[restart] Done at $(date)" >> "$LOG_FILE"
exit 0
