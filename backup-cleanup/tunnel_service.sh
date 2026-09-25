#!/data/data/com.termux/files/usr/bin/bash
# Tunnel Service - dikontrol dari dashboard
# Usage: ./tunnel_service.sh {start|stop|restart|status|url}

LOG_FILE="$HOME/capture-pro/tunnel.log"
PID_FILE="$HOME/capture-pro/tunnel.pid"

start_tunnel() {
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if kill -0 "$OLD_PID" 2>/dev/null; then
            echo "Tunnel sudah jalan (PID: $OLD_PID)"
            return 1
        fi
        rm -f "$PID_FILE"
    fi

    # Pastikan cloudflared ada
    if ! command -v cloudflared &> /dev/null; then
        echo "ERROR: cloudflared tidak terinstall"
        echo "Install: pkg install -y cloudflared"
        return 1
    fi

    cd "$HOME/capture-pro"
    nohup cloudflared tunnel --url http://localhost:8000 > "$LOG_FILE" 2>&1 &
    NEW_PID=$!
    echo $NEW_PID > "$PID_FILE"
    echo "Tunnel dijalankan (PID: $NEW_PID)"

    # Tunggu URL muncul (max 20 detik)
    for i in $(seq 1 20); do
        sleep 1
        URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$LOG_FILE" 2>/dev/null | head -1)
        if [ -n "$URL" ]; then
            echo "URL: $URL"
            return 0
        fi
    done
    echo "URL belum siap, cek log nanti"

    # Auto-set webhook after tunnel start
    if [ -f "$HOME/capture-pro/auto_webhook.sh" ]; then
        nohup bash "$HOME/capture-pro/auto_webhook.sh" > /dev/null 2>&1 &
        disown 2>/dev/null
    fi
}

stop_tunnel() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID" 2>/dev/null
            sleep 2
            kill -9 "$PID" 2>/dev/null
            rm -f "$PID_FILE"
            echo "Tunnel dihentikan (PID: $PID)"
        else
            rm -f "$PID_FILE"
            echo "Tunnel sudah tidak jalan"
        fi
    else
        echo "Tunnel tidak sedang jalan"
    fi
}

status_tunnel() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat $PID_FILE)" 2>/dev/null; then
        URL=$(grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$LOG_FILE" 2>/dev/null | head -1)
        echo "RUNNING|$(cat $PID_FILE)|$URL"
    else
        echo "STOPPED|0|"
    fi
}

case "$1" in
    start) start_tunnel ;;
    stop) stop_tunnel ;;
    restart) stop_tunnel; sleep 1; start_tunnel ;;
    status) status_tunnel ;;
    url) grep -o 'https://[a-z0-9-]*\.trycloudflare\.com' "$LOG_FILE" 2>/dev/null | head -1 ;;
    *) echo "Usage: $0 {start|stop|restart|status|url}" ;;
esac
