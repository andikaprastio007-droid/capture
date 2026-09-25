"""
Installer Tambahan: Auto-Start Tunnel + Utility Scripts
Jalankan: python setup_tunnel_autostart.py

Menyempurnakan setup_tunnel_button.py dengan:
  - Auto-start tunnel saat server start
  - Config file untuk toggle auto-start
  - Script utility (stop_all, status_all)
  - Alias di ~/.bashrc
"""
import os
from pathlib import Path

PROJECT = Path.home() / "capture-pro"
HOME = Path.home()

if not PROJECT.exists():
    print(f"❌ Folder {PROJECT} tidak ada.")
    exit(1)


# ============================================================
# 1. BIKIN auto_tunnel.conf
# ============================================================
print("[1/5] Bikin auto_tunnel.conf...")
conf_file = PROJECT / "auto_tunnel.conf"
if not conf_file.exists():
    conf_file.write_text("""# Auto-Start Tunnel Configuration
# Set ke true untuk auto-start tunnel saat server start
# Set ke false untuk manual control via dashboard

AUTO_START_TUNNEL=true

# Delay sebelum start tunnel (detik) — biar Flask siap dulu
START_DELAY=3
""", encoding="utf-8")
    print(f"  OK  {conf_file}")
else:
    print(f"  SKIP  {conf_file} sudah ada")


# ============================================================
# 2. PATCH run.py — tambah auto-start tunnel
# ============================================================
print("[2/5] Patch run.py...")
run_file = PROJECT / "run.py"
if run_file.exists():
    content = run_file.read_text(encoding="utf-8")

    # Backup
    backup = run_file.with_suffix(".py.bak_tunnel")
    backup.write_text(content, encoding="utf-8")

    if "auto_tunnel" not in content:
        # Sisipkan auto_tunnel sebelum `from app import create_app`
        auto_code = '''
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

'''
        content = content.replace("from app import create_app", auto_code + "from app import create_app")

        run_file.write_text(content, encoding="utf-8")
        print(f"  OK  {run_file} (backup: {backup.name})")
    else:
        print(f"  SKIP  run.py sudah di-patch")
else:
    print(f"  SKIP  run.py tidak ada")


# ============================================================
# 3. BIKIN stop_all.sh
# ============================================================
print("[3/5] Bikin stop_all.sh...")
stop_sh = PROJECT / "stop_all.sh"
stop_sh.write_text('''#!/data/data/com.termux/files/usr/bin/bash
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
''', encoding="utf-8")
stop_sh.chmod(0o755)
print(f"  OK  {stop_sh}")


# ============================================================
# 4. BIKIN status_all.sh
# ============================================================
print("[4/5] Bikin status_all.sh...")
status_sh = PROJECT / "status_all.sh"
status_sh.write_text('''#!/data/data/com.termux/files/usr/bin/bash
# Cek status server + tunnel

GREEN='\\033[0;32m'
RED='\\033[0;31m'
YELLOW='\\033[1;33m'
NC='\\033[0m'

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
''', encoding="utf-8")
status_sh.chmod(0o755)
print(f"  OK  {status_sh}")


# ============================================================
# 5. TAMBAH ALIAS DI ~/.bashrc
# ============================================================
print("[5/5] Tambah alias di ~/.bashrc...")
bashrc = HOME / ".bashrc"
alias_block = """
# ============ RECONPRO ALIASES ============
alias recon="cd ~/capture-pro && python run.py"
alias reconstop="bash ~/capture-pro/stop_all.sh"
alias reconstatus="bash ~/capture-pro/status_all.sh"
alias recontunnel="bash ~/capture-pro/tunnel_service.sh start"
alias recontunnel-stop="bash ~/capture-pro/tunnel_service.sh stop"
alias reconurl="bash ~/capture-pro/tunnel_service.sh url"
alias reconlog="tail -f ~/capture-pro/tunnel.log"
# =========================================
"""

if bashrc.exists():
    content = bashrc.read_text(encoding="utf-8")
    if "RECONPRO ALIASES" not in content:
        content += alias_block
        bashrc.write_text(content, encoding="utf-8")
        print(f"  OK  Alias ditambahkan ke {bashrc}")
    else:
        print(f"  SKIP  Alias sudah ada")
else:
    bashrc.write_text(alias_block, encoding="utf-8")
    print(f"  OK  {bashrc} dibuat")


# ============================================================
# DONE
# ============================================================
print()
print("=" * 60)
print("  ✅ INSTALL BERHASIL — Auto-Start Tunnel Aktif")
print("=" * 60)
print()
print("  Alias baru (jalankan dulu: source ~/.bashrc):")
print()
print("    recon            → start server + auto-tunnel")
print("    reconstop        → stop server + tunnel")
print("    reconstatus      → cek status semua")
print("    recontunnel      → start tunnel manual")
print("    recontunnel-stop → stop tunnel")
print("    reconurl         → lihat URL tunnel")
print("    reconlog         → lihat log tunnel realtime")
print()
print("  Cara pakai:")
print()
print("    1. Reload shell:")
print("         source ~/.bashrc")
print()
print("    2. Start server + tunnel:")
print("         recon")
print()
print("    3. Cek status (terminal lain):")
print("         reconstatus")
print()
print("  Config auto-start:")
print("    nano ~/capture-pro/auto_tunnel.conf")
print("    → AUTO_START_TUNNEL=true/false")
print()
print("  Buka dashboard:")
print("    http://localhost:8000/dashboard")
print("    Tombol '🌐 Tunnel' tetap bisa dipakai manual")
print()
