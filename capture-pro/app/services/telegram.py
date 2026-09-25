"""Telegram sender service."""
import requests
from app.config import Config


def send_text(text, parse_mode="HTML"):
    """Kirim pesan teks ke Telegram."""
    if not Config.TG_TOKEN or "ISI_" in Config.TG_TOKEN:
        print("[telegram] Token belum diisi")
        return False
    
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{Config.TG_TOKEN}/sendMessage",
            json={
                "chat_id": Config.TG_CHAT_ID,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": False,
            },
            timeout=15,
        )
        data = r.json()
        if not data.get("ok"):
            print(f"[telegram] Gagal: {data.get('description')}")
            return False
        return True
    except Exception as e:
        print(f"[telegram] Error: {e}")
        return False


def send_photo(image_bytes, caption=""):
    """Kirim foto ke Telegram."""
    if not Config.TG_TOKEN or "ISI_" in Config.TG_TOKEN:
        return False
    
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{Config.TG_TOKEN}/sendPhoto",
            data={"chat_id": Config.TG_CHAT_ID, "caption": caption},
            files={"photo": ("foto.png", image_bytes, "image/png")},
            timeout=20,
        )
        return r.json().get("ok", False)
    except Exception as e:
        print(f"[telegram] Photo error: {e}")
        return False


def send_telegram_text(text):
    """Alias untuk send_text (untuk kompatibilitas)."""
    return send_text(text)
