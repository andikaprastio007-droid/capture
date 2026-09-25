#!/data/data/com.termux/files/usr/bin/bash
# Restart server Flask — DETACHED version

PROJECT="$HOME/capture-pro"
LOG_FILE="$PROJECT/server.log"

cd "$PROJECT" || exit 1

{
    echo ""
    echo "========================================"
    echo "[restart] $(date)"
    echo "========================================"
} >> "$LOG_FILE" 2>&1

# Kill proses lama
pkill -f "python run.py" 2>/dev/null
sleep 3

# Force kill kalau bandel
pkill -9 -f "python run.py" 2>/dev/null
sleep 2

# Tunggu port bebas
for i in 1 2 3 4 5; do
    if ! netstat -tulpn 2>/dev/null | grep -q ":8000 "; then
        break
    fi
    sleep 1
done

echo "[restart] Port free, starting new server..." >> "$LOG_FILE"

# Start baru — detach TOTAL dari parent
# Gunakan setsid kalau ada
if command -v setsid >/dev/null 2>&1; then
    setsid python run.py >> "$LOG_FILE" 2>&1 < /dev/null &
else
    nohup python run.py >> "$LOG_FILE" 2>&1 < /dev/null &
    disown 2>/dev/null
fi

sleep 1
echo "[restart] Done at $(date)" >> "$LOG_FILE"

exit 0

# Auto-start watchdog
if ! ps aux 2>/dev/null | grep "watchdog.sh" | grep -v grep > /dev/null 2>&1; then
    nohup bash "$HOME/capture-pro/watchdog.sh" > /dev/null 2>&1 &
    disown 2>/dev/null
    echo "[start] Watchdog started" >> "$LOG_FILE"
fi
