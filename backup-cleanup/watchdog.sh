#!/data/data/com.termux/files/usr/bin/bash
# Watchdog Full Stack
# - Pantau server Flask
# - Pantau tunnel Cloudflared
# - Auto-restart yang mati
# - Auto-update webhook Telegram

LOG="$HOME/capture-pro/server.log"
PID_FILE="$HOME/capture-pro/watchdog.pid"
CHECK_INTERVAL=8

echo "$$" > "$PID_FILE"

log() {
    echo "[watchdog $(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG"
}

log "=========================================="
log "Watchdog started (PID: $$)"
log "=========================================="

# Fungsi: cek & restart server
check_server() {
    if ! ps aux 2>/dev/null | grep "python run.py" | grep -v grep > /dev/null 2>&1; then
        log "⚠️  Server Flask MATI — restart..."
        
        cd "$HOME/capture-pro" || return 1
        
        if command -v setsid >/dev/null 2>&1; then
            setsid python run.py >> "$LOG" 2>&1 < /dev/null &
        else
            nohup python run.py >> "$LOG" 2>&1 < /dev/null &
            disown 2>/dev/null
        fi
        
        sleep 6
        
        if ps aux 2>/dev/null | grep "python run.py" | grep -v grep > /dev/null 2>&1; then
            log "✅ Server Flask started"
            return 0
        else
            log "❌ Server Flask gagal start — cek log"
            return 1
        fi
    fi
    return 0
}

# Fungsi: cek & restart tunnel
check_tunnel() {
    if [ -f "$HOME/capture-pro/tunnel_service.sh" ]; then
        STATUS=$(bash "$HOME/capture-pro/tunnel_service.sh" status 2>/dev/null | cut -d'|' -f1)
        if [ "$STATUS" != "RUNNING" ]; then
            log "⚠️  Tunnel MATI — restart..."
            bash "$HOME/capture-pro/tunnel_service.sh" start >> "$LOG" 2>&1
            
            # Tunggu URL muncul
            sleep 12
            
            NEW_URL=$(bash "$HOME/capture-pro/tunnel_service.sh" url 2>/dev/null)
            if [ -n "$NEW_URL" ] && [ "$NEW_URL" != "STOPPED" ]; then
                log "✅ Tunnel started: $NEW_URL"
                # Update webhook
                update_webhook "$NEW_URL"
            else
                log "❌ Tunnel gagal start"
            fi
        fi
    fi
}

# Fungsi: update webhook Telegram
update_webhook() {
    local URL="$1"
    if [ -z "$URL" ]; then
        URL=$(bash "$HOME/capture-pro/tunnel_service.sh" url 2>/dev/null)
    fi
    
    if [ -z "$URL" ] || [ "$URL" = "STOPPED" ]; then
        log "⚠️  Tidak bisa update webhook — URL kosong"
        return 1
    fi
    
    if [ -f "$HOME/capture-pro/.env" ]; then
        TG_TOKEN=$(grep "^TG_TOKEN=" "$HOME/capture-pro/.env" | cut -d= -f2-)
        if [ -n "$TG_TOKEN" ]; then
            RESULT=$(curl -s -X POST "https://api.telegram.org/bot${TG_TOKEN}/setWebhook" \
                -H "Content-Type: application/json" \
                -d "{\"url\":\"${URL}/tg/webhook\"}" 2>/dev/null)
            
            if echo "$RESULT" | grep -q '"ok":true'; then
                log "✅ Webhook updated: ${URL}/tg/webhook"
            else
                log "⚠️  Webhook update gagal: $RESULT"
            fi
        fi
    fi
}

# ============================================================
# MAIN LOOP
# ============================================================
TICK=0

while true; do
    sleep $CHECK_INTERVAL
    TICK=$((TICK + 1))
    
    # Cek server
    check_server
    
    # Cek tunnel (setiap 4x cek server = ~32 detik)
    if [ $((TICK % 4)) -eq 0 ]; then
        check_tunnel
    fi
done
