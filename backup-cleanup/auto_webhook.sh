#!/data/data/com.termux/files/usr/bin/bash
# Auto-set webhook setelah tunnel start (dipanggil oleh tunnel_service.sh)

sleep 8
cd "$HOME/capture-pro" || exit 1
bash set-webhook.sh >> ~/capture-pro/webhook.log 2>&1
