#!/data/data/com.termux/files/usr/bin/bash

# Warna
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PORT=${1:-8000}

echo -e "${YELLOW}[*] Stopping existing server...${NC}"

# Kill semua yang mungkin pakai port
pkill -f "python run.py" 2>/dev/null
pkill -f "python app.py" 2>/dev/null
pkill -f "flask run" 2>/dev/null

# Kill by port
if command -v fuser &> /dev/null; then
    fuser -k ${PORT}/tcp 2>/dev/null
fi

sleep 2

# Cek port bebas
if netstat -tulpn 2>/dev/null | grep -q ":${PORT} "; then
    echo -e "${RED}[!] Port ${PORT} masih dipakai. Coba kill manual:${NC}"
    netstat -tulpn 2>/dev/null | grep ":${PORT} "
    exit 1
fi

echo -e "${GREEN}[✓] Port ${PORT} bebas${NC}"

# Jalanin server
cd ~/capture-pro
echo -e "${GREEN}[✓] Starting server on port ${PORT}...${NC}"
echo ""
exec python run.py
