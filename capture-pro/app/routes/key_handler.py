"""Telegram Handler — Minta key editor via bot."""
from flask import Blueprint, jsonify, request
from app.config import Config
from app.routes.capture import send_telegram_text as send_text
import os

bp = Blueprint("key_handler", __name__)


def _is_admin(chat_id):
    """Cek apakah chat_id termasuk admin."""
    admins = Config.TELEGRAM_ADMIN_ID or ""
    if not admins:
        return False
    allowed = [x.strip() for x in admins.split(",") if x.strip()]
    return str(chat_id) in allowed


def _get_editor_key():
    """Ambil editor key dari env."""
    return Config.EDITOR_SECRET_KEY or ""


def _get_base_url():
    """Ambil base URL (tunnel atau localhost)."""
    # Coba baca dari tunnel_service
    import subprocess
    try:
        script = os.path.expanduser("~/capture-pro/tunnel_service.sh")
        if os.path.isfile(script):
            result = subprocess.run(
                ["bash", script, "url"],
                capture_output=True, text=True, timeout=5,
            )
            url = (result.stdout or "").strip()
            if url.startswith("https://"):
                return url.rstrip("/")
    except Exception:
        pass
    return "http://localhost:8000"


@bp.route("/key-webhook", methods=["POST"])
def key_webhook():
    """Handle pesan Telegram untuk minta key."""
    update = request.get_json(silent=True) or {}
    msg = update.get("message") or update.get("edited_message") or {}
    text = (msg.get("text") or "").strip()
    chat_id = msg.get("chat", {}).get("id")
    from_user = msg.get("from", {}).get("username") or msg.get("from", {}).get("first_name") or "User"

    if not chat_id:
        return jsonify({"ok": True})

    # ==== Command: /key ====
    if text in ("/key", "/editor-key", "/key@bot", "/getkey"):
        if not _is_admin(chat_id):
            # Untuk non-admin: diam atau kasih pesan generik
            return jsonify({"ok": True})

        key = _get_editor_key()
        if not key:
            send_text(
                "⚠️ <b>Key editor belum di-set</b>\n\n"
                "Set di <code>~/capture-pro/.env</code>:\n"
                "<code>EDITOR_SECRET_KEY=key_kamu</code>"
            )
            return jsonify({"ok": True})

        base = _get_base_url()
        link = f"{base}/editor?key={key}"

        send_text(
            "🔑 <b>Secret Editor Key</b>\n\n"
            f"<code>{key}</code>\n\n"
            f"🔗 <b>Link akses:</b>\n"
            f"<a href=\"{link}\">{link}</a>\n\n"
            "⚠️ <i>Jangan share key ini ke siapapun</i>"
        )
        return jsonify({"ok": True})

    # ==== Command: /link ====
    if text in ("/link", "/editor-link"):
        if not _is_admin(chat_id):
            return jsonify({"ok": True})

        key = _get_editor_key()
        if not key:
            send_text("⚠️ Key editor belum di-set.")
            return jsonify({"ok": True})

        base = _get_base_url()
        link = f"{base}/editor?key={key}"

        send_text(
            f"🔗 <b>Link Editor</b>\n\n"
            f"<a href=\"{link}\">{link}</a>\n\n"
            "Klik link di atas untuk buka editor."
        )
        return jsonify({"ok": True})

    # ==== Command: /help ====
    if text in ("/help", "/start"):
        send_text(
            "<b>Commands:</b>\n\n"
            "/key — Minta secret key editor\n"
            "/link — Link langsung ke editor\n"
            "/reset — Generate key baru\n"
            "/status — Cek konfigurasi"
        )
        return jsonify({"ok": True})

    # ==== Command: /status ====
    if text == "/status":
        if not _is_admin(chat_id):
            return jsonify({"ok": True})

        key = _get_editor_key()
        base = _get_base_url()
        send_text(
            "<b>Status:</b>\n\n"
            f"Key set: {'✅' if key else '❌'}\n"
            f"Base URL: {base}\n"
            f"Admin: {Config.TELEGRAM_ADMIN_ID}"
        )
        return jsonify({"ok": True})

    # ==== Command: /reset ====
    if text == "/reset":
        if not _is_admin(chat_id):
            return jsonify({"ok": True})

        import secrets
        new_key = secrets.token_urlsafe(24)

        # Update .env
        env_path = os.path.expanduser("~/capture-pro/.env")
        try:
            content = ""
            if os.path.isfile(env_path):
                with open(env_path, "r") as f:
                    content = f.read()

            if "EDITOR_SECRET_KEY=" in content:
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if line.startswith("EDITOR_SECRET_KEY="):
                        lines[i] = f"EDITOR_SECRET_KEY={new_key}"
                        break
                content = "\n".join(lines)
            else:
                content += f"\n\nEDITOR_SECRET_KEY={new_key}\n"

            with open(env_path, "w") as f:
                f.write(content)

            # Update runtime
            Config.EDITOR_SECRET_KEY = new_key

            send_text(
                "🔑 <b>Key Baru:</b>\n\n"
                f"<code>{new_key}</code>\n\n"
                "⚠️ <i>Server perlu restart agar key berlaku penuh.</i>\n"
                "Restart: /editor bisa tapi restart server via dashboard."
            )
        except Exception as e:
            send_text(f"❌ Gagal update key: {e}")

        return jsonify({"ok": True})



# ==== COMMAND: /restart ====
    if text in ("/restart", "/reload", "/reboot"):
        if not _is_admin(chat_id):
            return jsonify({"ok": True})

        # Kirim notif dulu SEBELUM restart
        send_text(
            "🔄 <b>Restarting server...</b>\n\n"
            "Server akan restart dalam 3-5 detik.\n"
            "Tunggu pesan konfirmasi."
        )

        # Jalankan restart script DETACHED
        try:
            import subprocess
            script = os.path.expanduser("~/capture-pro/restart_server.sh")
            
            if not os.path.isfile(script):
                send_text("⚠️ restart_server.sh tidak ditemukan")
                return jsonify({"ok": True})
            
            # DETACH total dari Flask
            import shutil
            if shutil.which("setsid"):
                cmd = ["setsid", "bash", script]
            else:
                cmd = ["nohup", "bash", script]
            
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                start_new_session=True,
                close_fds=True,
                cwd=os.path.expanduser("~/capture-pro"),
            )
            print(f"[restart] triggered via Telegram, PID {proc.pid}")
            
            # Catat ke log
            try:
                with open(os.path.expanduser("~/capture-pro/server.log"), "a") as f:
                    f.write(f"\n[restart-tg] Triggered at $(date)\n")
            except Exception:
                pass
                
        except Exception as e:
            send_text(f"❌ Gagal trigger restart: {e}")

        return jsonify({"ok": True})

        send_text(
            "🔄 <b>Restarting server...</b>\n\n"
            "Server akan restart dalam 3-5 detik.\n"
            "Tunggu, nanti bot balas lagi."
        )

        # Restart di background
        try:
            import subprocess
            script = os.path.expanduser("~/capture-pro/restart_server.sh")
            if os.path.isfile(script):
                proc = subprocess.Popen(
                    ["bash", script],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    stdin=subprocess.DEVNULL,
                    start_new_session=True,
                    close_fds=True,
                )
                print(f"[restart] triggered via Telegram, PID {proc.pid}")
            else:
                send_text("⚠️ restart_server.sh tidak ada")
        except Exception as e:
            send_text(f"❌ Gagal restart: {e}")

        return jsonify({"ok": True})

    # ==== COMMAND: /uptime ====
    if text in ("/uptime", "/up"):
        if not _is_admin(chat_id):
            return jsonify({"ok": True})

        try:
            import time as _t
            import subprocess as _sp
            
            uptime_str = "N/A"
            
            # Coba 1: baca /proc/uptime (kalau diizinkan)
            try:
                with open("/proc/uptime") as f:
                    sec = float(f.read().split()[0])
                d = int(sec // 86400)
                h = int((sec % 86400) // 3600)
                m = int((sec % 3600) // 60)
                uptime_str = f"{d}h {h}j {m}m"
            except (PermissionError, FileNotFoundError):
                # Coba 2: pakai command uptime
                try:
                    result = _sp.run(["uptime"], capture_output=True, text=True, timeout=5)
                    uptime_str = result.stdout.strip() or "N/A"
                except Exception:
                    # Coba 3: fallback ke waktu server start
                    try:
                        result = _sp.run(["ps", "-o", "etime=", "-p", "1"],
                                         capture_output=True, text=True, timeout=5)
                        uptime_str = result.stdout.strip() or "N/A"
                    except Exception:
                        uptime_str = "Tidak bisa dibaca"
            
            # Info tambahan: proses server
            try:
                result = _sp.run(["pgrep", "-f", "python run.py"],
                                 capture_output=True, text=True, timeout=5)
                py_pids = [p for p in result.stdout.strip().split("\n") if p]
                proc_info = f"{len(py_pids)} proses Python"
            except Exception:
                proc_info = "?"
            
            send_text(
                f"⏱️ <b>Uptime Server</b>\n\n"
                f"<b>Server uptime:</b> {uptime_str}\n"
                f"<b>Proses:</b> {proc_info}"
            )
        except Exception as e:
            send_text(f"⚠️ Gagal cek uptime: {e}")

        return jsonify({"ok": True})

    # ==== COMMAND: /sysinfo ====
    if text in ("/sysinfo", "/sys", "/info"):
        if not _is_admin(chat_id):
            return jsonify({"ok": True})

        try:
            import subprocess as _sp
            
            # RAM
            with open("/proc/meminfo") as f:
                mem_info = {}
                for line in f:
                    parts = line.split()
                    if parts:
                        mem_info[parts[0].rstrip(":")] = int(parts[1])
            
            total_mb = mem_info.get("MemTotal", 0) / 1024
            avail_mb = mem_info.get("MemAvailable", 0) / 1024
            used_mb = total_mb - avail_mb
            pct = (used_mb / total_mb * 100) if total_mb > 0 else 0
            
            # Disk
            try:
                result = _sp.run(["df", "-h", os.path.expanduser("~/capture-pro")],
                                 capture_output=True, text=True, timeout=5)
                disk_line = result.stdout.strip().split("\n")[-1]
                disk_parts = disk_line.split()
                disk_info = f"{disk_parts[2]} / {disk_parts[1]} ({disk_parts[4]})"
            except Exception:
                disk_info = "N/A"
            
            # Jumlah sesi
            try:
                from app.models import Session as S
                session_count = S.query.count()
            except Exception:
                session_count = "N/A"
            
            # Proses python
            try:
                result = _sp.run(["pgrep", "-f", "python run.py"],
                                 capture_output=True, text=True, timeout=5)
                py_pids = result.stdout.strip().split("\n")
                py_count = len([p for p in py_pids if p])
            except Exception:
                py_count = "?"
            
            send_text(
                f"💻 <b>System Info</b>\n\n"
                f"🧠 RAM: {used_mb:.0f} MB / {total_mb:.0f} MB ({pct:.1f}%)\n"
                f"💾 Disk: {disk_info}\n"
                f"📊 Sesi tersimpan: {session_count}\n"
                f"🐍 Proses Python: {py_count}\n"
            )
        except Exception as e:
            send_text(f"⚠️ Gagal cek sysinfo: {e}")

        return jsonify({"ok": True})

    # ==== COMMAND: /tunnel ====
    if text in ("/tunnel", "/url"):
        if not _is_admin(chat_id):
            return jsonify({"ok": True})

        try:
            import subprocess as _sp
            script = os.path.expanduser("~/capture-pro/tunnel_service.sh")
            result = _sp.run(["bash", script, "status"],
                             capture_output=True, text=True, timeout=10)
            parts = result.stdout.strip().split("|")
            running = parts[0] == "RUNNING"
            url = parts[2] if len(parts) > 2 else ""
            
            if running and url:
                send_text(
                    f"🌐 <b>Tunnel Aktif</b>\n\n"
                    f"<a href=\"{url}\">{url}</a>"
                )
            else:
                send_text("⚠️ Tunnel tidak aktif")
        except Exception as e:
            send_text(f"⚠️ Gagal cek tunnel: {e}")

        return jsonify({"ok": True})

    return jsonify({"ok": True})
