#!/data/data/com.termux/files/usr/bin/bash
# Stop semua: server + tunnel
echo "[*] Stopping everything..."

# Stop tunnel
if [ -f "$HOME/capture-pro/tunnel_service.sh" ]; then
    bash "$HOME/capture-pro/tunnel_service.sh" stop 2>/dev/null
fi

# Stop Flask server
pkill -f "python run.py" 2>/dev/null
pkill -f "python app.py" 2>/dev/null

sleep 1

# Cek
if netstat -tulpn 2>/dev/null | grep -q ":8000 "; then
    echo "[!] Port 8000 masih dipakai"
else
    echo "[✓] Port 8000 bebas"
fi

echo "[✓] Done"
