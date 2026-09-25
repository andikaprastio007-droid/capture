#!/data/data/com.termux/files/usr/bin/bash
# Cek status server + tunnel

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}=== Status ===${NC}"
echo ""

# Server
if netstat -tulpn 2>/dev/null | grep -q ":8000 "; then
    PID=$(netstat -tulpn 2>/dev/null | grep ":8000 " | awk '{print $7}' | cut -d/ -f1 | head -1)
    echo -e "  Flask Server : ${GREEN}RUNNING${NC} (port 8000, PID: $PID)"
else
    echo -e "  Flask Server : ${RED}STOPPED${NC}"
fi

# Tunnel
if [ -f "$HOME/capture-pro/tunnel_service.sh" ]; then
    OUT=$(bash "$HOME/capture-pro/tunnel_service.sh" status 2>/dev/null)
    RUNNING=$(echo "$OUT" | cut -d'|' -f1)
    PID=$(echo "$OUT" | cut -d'|' -f2)
    URL=$(echo "$OUT" | cut -d'|' -f3)
    if [ "$RUNNING" = "RUNNING" ]; then
        echo -e "  Tunnel       : ${GREEN}RUNNING${NC} (PID: $PID)"
        if [ -n "$URL" ]; then
            echo -e "  Public URL   : ${GREEN}$URL${NC}"
        else
            echo -e "  Public URL   : ${YELLOW}(belum tersedia)${NC}"
        fi
    else
        echo -e "  Tunnel       : ${RED}STOPPED${NC}"
    fi
fi

# IP lokal
IP=$(ifconfig 2>/dev/null | grep "inet " | grep -v 127.0.0.1 | awk '{print $2}' | head -1)
if [ -n "$IP" ]; then
    echo ""
    echo -e "  ${YELLOW}Local URL${NC}    : http://$IP:8000/"
fi

# Cloudflared install check
if command -v cloudflared &> /dev/null; then
    VERSION=$(cloudflared --version 2>/dev/null | head -1)
    echo ""
    echo -e "  Cloudflared  : ${GREEN}$VERSION${NC}"
else
    echo ""
    echo -e "  Cloudflared  : ${RED}NOT INSTALLED${NC}"
fi

echo ""
