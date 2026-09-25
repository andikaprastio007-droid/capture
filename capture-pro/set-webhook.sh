#!/data/data/com.termux/files/usr/bin/bash
# Set webhook Telegram otomatis ke URL tunnel aktif

PROJECT="$HOME/capture-pro"
cd "$PROJECT" || exit 1

# Load env
if [ ! -f .env ]; then
    echo "❌ .env tidak ada"
    exit 1
fi

export $(grep -v '^#' .env | grep -E '^(TG_TOKEN|TG_CHAT_ID)=' | xargs)

if [ -z "$TG_TOKEN" ]; then
    echo "❌ TG_TOKEN kosong di .env"
    exit 1
fi

echo "=== Set Webhook Telegram ==="
echo ""

# Cek tunnel
TUNNEL_URL=$(bash tunnel_service.sh url 2>/dev/null)

if [ -z "$TUNNEL_URL" ] || [ "$TUNNEL_URL" = "STOPPED" ]; then
    echo "⚠️  Tunnel belum jalan, start..."
    bash tunnel_service.sh start
    echo "Tunggu 15 detik..."
    sleep 15
    TUNNEL_URL=$(bash tunnel_service.sh url 2>/dev/null)
fi

if [ -z "$TUNNEL_URL" ]; then
    echo "❌ Tunnel URL kosong"
    echo "   Coba: cd ~/capture-pro && ./tunnel_service.sh status"
    exit 1
fi

echo "🔗 Tunnel URL: $TUNNEL_URL"
echo ""

# Set webhook
WEBHOOK_URL="${TUNNEL_URL}/tg/webhook"
echo "📡 Set webhook ke: $WEBHOOK_URL"
echo ""

RESULT=$(curl -s -X POST "https://api.telegram.org/bot${TG_TOKEN}/setWebhook" \
    -H "Content-Type: application/json" \
    -d "{\"url\":\"${WEBHOOK_URL}\"}")

echo "$RESULT" | python3 -m json.tool 2>/dev/null || echo "$RESULT"
echo ""

# Verifikasi
sleep 2
echo "📋 Verifikasi:"
curl -s "https://api.telegram.org/bot${TG_TOKEN}/getWebhookInfo" | python3 -m json.tool
echo ""

echo "✅ SELESAI"
echo ""
echo "   Coba kirim /start atau /help di Telegram bot kamu"
