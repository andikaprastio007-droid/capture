#!/data/data/com.termux/files/usr/bin/bash
# Cek status semua service

echo ""
echo "╔════════════════════════════════════════╗"
echo "║   ReconPro — Status                    ║"
echo "╚════════════════════════════════════════╝"
echo ""

# Server
if ps aux 2>/dev/null | grep "python run.py" | grep -v grep > /dev/null 2>&1; then
    PID=$(ps aux 2>/dev/null | grep "python run.py" | grep -v grep | awk '{print $2}' | head -1)
    echo "  ✅ Flask Server   RUNNING (PID: $PID)"
else
    echo "  ❌ Flask Server   STOPPED"
fi

# Watchdog
WATCHDOG_PID=$(cat "$HOME/capture-pro/watchdog.pid" 2>/dev/null)
if [ -n "$WATCHDOG_PID" ] && kill -0 "$WATCHDOG_PID" 2>/dev/null; then
    echo "  ✅ Watchdog       RUNNING (PID: $WATCHDOG_PID)"
else
    echo "  ❌ Watchdog       STOPPED"
fi

# Tunnel
TUNNEL_STATUS=$(bash "$HOME/capture-pro/tunnel_service.sh" status 2>/dev/null | cut -d'|' -f1)
TUNNEL_URL=$(bash "$HOME/capture-pro/tunnel_service.sh" url 2>/dev/null)
if [ "$TUNNEL_STATUS" = "RUNNING" ]; then
    echo "  ✅ Tunnel         RUNNING"
    if [ -n "$TUNNEL_URL" ]; then
        echo "     🌍 URL: $TUNNEL_URL"
    fi
else
    echo "  ❌ Tunnel         STOPPED"
fi

# Webhook
if [ -f "$HOME/capture-pro/.env" ]; then
    TG_TOKEN=$(grep "^TG_TOKEN=" "$HOME/capture-pro/.env" | cut -d= -f2-)
    if [ -n "$TG_TOKEN" ]; then
        WH_INFO=$(curl -s "https://api.telegram.org/bot${TG_TOKEN}/getWebhookInfo" 2>/dev/null)
        WH_URL=$(echo "$WH_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin).get('result',{}).get('url',''))" 2>/dev/null)
        WH_PENDING=$(echo "$WH_INFO" | python3 -c "import sys,json; print(json.load(sys.stdin).get('result',{}).get('pending_update_count',0))" 2>/dev/null)
        
        if [ -n "$WH_URL" ]; then
            echo "  ✅ Webhook        SET"
            echo "     🔗 $WH_URL"
            echo "     ⏳ Pending: $WH_PENDING"
        else
            echo "  ❌ Webhook        NOT SET"
        fi
    fi
fi

# Wake lock
if command -v termux-wake-lock >/dev/null 2>&1; then
    if pgrep -f "termux-wake-lock" > /dev/null 2>&1; then
        echo "  ✅ Wake Lock      AKTIF"
    else
        echo "  ⚠️  Wake Lock      TIDAK AKTIF"
    fi
fi

echo ""
echo "  📄 Log: tail -f ~/capture-pro/server.log"
echo ""
