"""
Installer: Tombol "Start Tunnel" di Dashboard
Otomatis bikin:
  - tunnel_service.sh
  - app/routes/tunnel.py
  - Patch app/__init__.py
  - Patch dashboard.html (tombol + panel)
  - Patch style.css (CSS panel)
  - Patch dashboard.js (JS control)
Jalankan: python setup_tunnel_button.py
"""
import os
import shutil
from pathlib import Path

PROJECT = Path.home() / "capture-pro"

if not PROJECT.exists():
    print(f"❌ Folder {PROJECT} tidak ada. Jalankan installer capture-pro dulu.")
    exit(1)

# ============================================================
# 1. BIKIN tunnel_service.sh
# ============================================================
print("[1/6] Bikin tunnel_service.sh...")
sh_path = PROJECT / "tunnel_service.sh"
sh_path.write_text('''#!/data/data/com.termux/files/usr/bin/bash
# Tunnel Service - dikontrol dari dashboard
# Usage: ./tunnel_service.sh {start|stop|restart|status|url}

LOG_FILE="$HOME/capture-pro/tunnel.log"
PID_FILE="$HOME/capture-pro/tunnel.pid"

start_tunnel() {
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if kill -0 "$OLD_PID" 2>/dev/null; then
            echo "Tunnel sudah jalan (PID: $OLD_PID)"
            return 1
        fi
        rm -f "$PID_FILE"
    fi

    # Pastikan cloudflared ada
    if ! command -v cloudflared &> /dev/null; then
        echo "ERROR: cloudflared tidak terinstall"
        echo "Install: pkg install -y cloudflared"
        return 1
    fi

    cd "$HOME/capture-pro"
    nohup cloudflared tunnel --url http://localhost:8000 > "$LOG_FILE" 2>&1 &
    NEW_PID=$!
    echo $NEW_PID > "$PID_FILE"
    echo "Tunnel dijalankan (PID: $NEW_PID)"

    # Tunggu URL muncul (max 20 detik)
    for i in $(seq 1 20); do
        sleep 1
        URL=$(grep -o 'https://[a-z0-9-]*\\.trycloudflare\\.com' "$LOG_FILE" 2>/dev/null | head -1)
        if [ -n "$URL" ]; then
            echo "URL: $URL"
            return 0
        fi
    done
    echo "URL belum siap, cek log nanti"
}

stop_tunnel() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID" 2>/dev/null
            sleep 2
            kill -9 "$PID" 2>/dev/null
            rm -f "$PID_FILE"
            echo "Tunnel dihentikan (PID: $PID)"
        else
            rm -f "$PID_FILE"
            echo "Tunnel sudah tidak jalan"
        fi
    else
        echo "Tunnel tidak sedang jalan"
    fi
}

status_tunnel() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat $PID_FILE)" 2>/dev/null; then
        URL=$(grep -o 'https://[a-z0-9-]*\\.trycloudflare\\.com' "$LOG_FILE" 2>/dev/null | head -1)
        echo "RUNNING|$(cat $PID_FILE)|$URL"
    else
        echo "STOPPED|0|"
    fi
}

case "$1" in
    start) start_tunnel ;;
    stop) stop_tunnel ;;
    restart) stop_tunnel; sleep 1; start_tunnel ;;
    status) status_tunnel ;;
    url) grep -o 'https://[a-z0-9-]*\\.trycloudflare\\.com' "$LOG_FILE" 2>/dev/null | head -1 ;;
    *) echo "Usage: $0 {start|stop|restart|status|url}" ;;
esac
''', encoding="utf-8")
sh_path.chmod(0o755)
print(f"  OK  {sh_path}")

# ============================================================
# 2. BIKIN app/routes/tunnel.py
# ============================================================
print("[2/6] Bikin app/routes/tunnel.py...")
routes_dir = PROJECT / "app" / "routes"
routes_dir.mkdir(parents=True, exist_ok=True)
tunnel_route = routes_dir / "tunnel.py"

tunnel_route.write_text('''from flask import Blueprint, jsonify, request
from app.auth import login_required
import subprocess
import os

bp = Blueprint("tunnel", __name__)

SCRIPT = os.path.expanduser("~/capture-pro/tunnel_service.sh")
LOG_FILE = os.path.expanduser("~/capture-pro/tunnel.log")


def _run(args):
    """Jalankan tunnel_service.sh dengan argumen."""
    if not os.path.isfile(SCRIPT):
        return "ERROR: tunnel_service.sh tidak ditemukan"
    try:
        result = subprocess.run(
            ["bash", SCRIPT] + args,
            capture_output=True,
            text=True,
            timeout=30,
        )
        out = (result.stdout or "") + (result.stderr or "")
        return out.strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return "TIMEOUT"
    except Exception as e:
        return f"ERROR: {e}"


@bp.route("/tunnel/start", methods=["POST"])
@login_required
def tunnel_start():
    out = _run(["start"])
    return jsonify({"ok": True, "msg": out})


@bp.route("/tunnel/stop", methods=["POST"])
@login_required
def tunnel_stop():
    out = _run(["stop"])
    return jsonify({"ok": True, "msg": out})


@bp.route("/tunnel/restart", methods=["POST"])
@login_required
def tunnel_restart():
    out = _run(["restart"])
    return jsonify({"ok": True, "msg": out})


@bp.route("/tunnel/status", methods=["GET"])
@login_required
def tunnel_status():
    out = _run(["status"])
    parts = out.split("|")
    running = (parts[0].strip() == "RUNNING") if parts else False
    pid = parts[1].strip() if len(parts) > 1 else "0"
    url = parts[2].strip() if len(parts) > 2 else ""
    return jsonify({
        "ok": True,
        "running": running,
        "pid": pid,
        "url": url,
    })


@bp.route("/tunnel/url", methods=["GET"])
@login_required
def tunnel_url():
    out = _run(["url"])
    return jsonify({"ok": True, "url": out})


@bp.route("/tunnel/log", methods=["GET"])
@login_required
def tunnel_log():
    try:
        if os.path.isfile(LOG_FILE):
            with open(LOG_FILE, "r", errors="ignore") as f:
                lines = f.readlines()[-60:]
            return jsonify({"ok": True, "log": "".join(lines)})
        return jsonify({"ok": True, "log": "Belum ada log"})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)})
''', encoding="utf-8")
print(f"  OK  {tunnel_route}")

# ============================================================
# 3. PATCH app/__init__.py
# ============================================================
print("[3/6] Patch app/__init__.py...")
init_file = PROJECT / "app" / "__init__.py"
if init_file.exists():
    content = init_file.read_text(encoding="utf-8")

    # Backup
    backup = init_file.with_suffix(".py.bak2")
    backup.write_text(content, encoding="utf-8")

    # Tambah csrf.exempt untuk tunnel
    if "csrf.exempt(tunnel_mod.bp)" not in content:
        if "from app.routes import capture as capture_mod" in content:
            content = content.replace(
                "from app.routes import capture as capture_mod\n    csrf.exempt(capture_mod.bp)",
                "from app.routes import capture as capture_mod\n    csrf.exempt(capture_mod.bp)\n\n    from app.routes import tunnel as tunnel_mod\n    csrf.exempt(tunnel_mod.bp)"
            )
        else:
            # Fallback: cari baris csrf.init_app atau db.init_app
            content = content.replace(
                "db.init_app(app)",
                "db.init_app(app)\n\n    from app.routes import tunnel as tunnel_mod\n    csrf.exempt(tunnel_mod.bp)"
            )

    # Tambah import blueprint
    if "from app.routes.tunnel import bp as tunnel_bp" not in content:
        if "from app.routes.api import bp as api_bp" in content:
            content = content.replace(
                "from app.routes.api import bp as api_bp",
                "from app.routes.api import bp as api_bp\n    from app.routes.tunnel import bp as tunnel_bp"
            )

    # Register blueprint
    if "app.register_blueprint(tunnel_bp" not in content:
        if 'app.register_blueprint(api_bp, url_prefix="/api")' in content:
            content = content.replace(
                'app.register_blueprint(api_bp, url_prefix="/api")',
                'app.register_blueprint(api_bp, url_prefix="/api")\n    app.register_blueprint(tunnel_bp, url_prefix="/api")'
            )

    init_file.write_text(content, encoding="utf-8")
    print(f"  OK  {init_file} (backup: {backup.name})")
else:
    print("  SKIP  app/__init__.py tidak ada")

# ============================================================
# 4. PATCH dashboard.html — tombol + panel
# ============================================================
print("[4/6] Patch dashboard.html...")
dash_file = PROJECT / "app" / "templates" / "dashboard.html"
if dash_file.exists():
    content = dash_file.read_text(encoding="utf-8")

    # Backup
    backup = dash_file.with_suffix(".html.bak2")
    backup.write_text(content, encoding="utf-8")

    # Tambah tombol hijau "Tunnel" sebelum tombol Logout
    if 'id="btnTunnel"' not in content:
        if '<a class="btn red" href="/logout">Logout</a>' in content:
            content = content.replace(
                '<a class="btn red" href="/logout">Logout</a>',
                '<button class="btn green" id="btnTunnel">🌐 Tunnel</button>\n    <a class="btn red" href="/logout">Logout</a>'
            )

    # Tambah panel tunnel setelah </header>
    if 'id="tunnelPanel"' not in content:
        panel_html = '''
<!-- Panel Tunnel -->
<section class="tunnel-panel" id="tunnelPanel">
  <h3>🌐 Cloudflare Tunnel Control</h3>
  <div class="tunnel-status-row">
    <span class="tunnel-status-dot off" id="tunnelDot"></span>
    <span id="tunnelStatusText" style="font-size:13px">Memeriksa...</span>
    <span id="tunnelPid" style="color:#6e7681;font-size:11px"></span>
  </div>
  <div class="tunnel-url" id="tunnelUrl">-</div>
  <div class="btn-group" style="margin-top:12px">
    <button class="btn-sm start" id="btnTunnelStart">▶ Start</button>
    <button class="btn-sm stop" id="btnTunnelStop">⏹ Stop</button>
    <button class="btn-sm refresh" id="btnTunnelRefresh">🔄 Refresh</button>
    <button class="btn-sm refresh" id="btnTunnelCopy">📋 Copy URL</button>
  </div>
  <div class="tunnel-log" id="tunnelLog">Loading log...</div>
</section>
'''
        # Sisipkan setelah </header>
        if "</header>" in content:
            content = content.replace("</header>", "</header>\n" + panel_html, 1)

    dash_file.write_text(content, encoding="utf-8")
    print(f"  OK  {dash_file} (backup: {backup.name})")
else:
    print("  SKIP  dashboard.html tidak ada")

# ============================================================
# 5. PATCH style.css — tambah CSS tunnel panel
# ============================================================
print("[5/6] Patch style.css...")
css_file = PROJECT / "app" / "static" / "css" / "style.css"
if css_file.exists():
    content = css_file.read_text(encoding="utf-8")

    if ".tunnel-panel" not in content:
        css_extra = """

/* ============ TUNNEL PANEL ============ */
.btn.green { background: #2ea043; color: #fff; }

.tunnel-panel {
  background: #161b22;
  border: 1px solid #21262d;
  padding: 18px;
  border-radius: 10px;
  margin: 0 24px 20px;
  display: none;
}
.tunnel-panel.active { display: block; }
.tunnel-panel h3 {
  margin: 0 0 14px;
  font-size: 14px;
  color: #2ea043;
  letter-spacing: 0.5px;
}
.tunnel-status-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.tunnel-status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.tunnel-status-dot.on {
  background: #2ea043;
  box-shadow: 0 0 8px #2ea043;
  animation: pulse-tunnel 2s infinite;
}
.tunnel-status-dot.off { background: #da3633; }
@keyframes pulse-tunnel {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}
.tunnel-url {
  background: #0d1117;
  padding: 12px;
  border-radius: 6px;
  font-family: monospace;
  font-size: 13px;
  word-break: break-all;
  color: #58a6ff;
  border: 1px solid #21262d;
}
.tunnel-url a { color: #58a6ff; text-decoration: none; }
.tunnel-url a:hover { text-decoration: underline; }
.tunnel-log {
  background: #0d1117;
  padding: 12px;
  border-radius: 6px;
  font-family: monospace;
  font-size: 11px;
  max-height: 200px;
  overflow: auto;
  color: #8b949e;
  white-space: pre-wrap;
  margin-top: 12px;
  border: 1px solid #21262d;
  line-height: 1.5;
}
.btn-group { display: flex; gap: 8px; flex-wrap: wrap; }
.btn-sm {
  padding: 8px 14px;
  font-size: 13px;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  color: #fff;
  font-weight: 500;
  transition: opacity 0.15s;
}
.btn-sm:hover { opacity: 0.85; }
.btn-sm.start { background: #2ea043; }
.btn-sm.stop { background: #da3633; }
.btn-sm.refresh { background: #30363d; }
"""
        content += css_extra
        css_file.write_text(content, encoding="utf-8")
        print(f"  OK  {css_file}")
    else:
        print("  SKIP  CSS sudah ada")
else:
    print("  SKIP  style.css tidak ada")

# ============================================================
# 6. PATCH dashboard.js — tambah JS control
# ============================================================
print("[6/6] Patch dashboard.js...")
js_file = PROJECT / "app" / "static" / "js" / "dashboard.js"
if js_file.exists():
    content = js_file.read_text(encoding="utf-8")

    if "startTunnel" not in content:
        js_extra = r"""

// ============================================================
// TUNNEL CONTROL
// ============================================================
(function() {
  const panel = document.getElementById('tunnelPanel');
  const btnMain = document.getElementById('btnTunnel');
  if (!panel || !btnMain) return;

  const dot = document.getElementById('tunnelDot');
  const statusText = document.getElementById('tunnelStatusText');
  const pidText = document.getElementById('tunnelPid');
  const urlEl = document.getElementById('tunnelUrl');
  const logEl = document.getElementById('tunnelLog');

  btnMain.addEventListener('click', () => {
    panel.classList.toggle('active');
    if (panel.classList.contains('active')) {
      refreshTunnel();
      loadTunnelLog();
    }
  });

  async function refreshTunnel() {
    try {
      const res = await fetch('/api/tunnel/status');
      const data = await res.json();
      if (data.running) {
        dot.className = 'tunnel-status-dot on';
        statusText.textContent = 'Running';
        statusText.style.color = '#2ea043';
        pidText.textContent = 'PID: ' + data.pid;
        if (data.url) {
          urlEl.innerHTML = '🔗 <a href="' + data.url + '" target="_blank">' + data.url + '</a>';
        } else {
          urlEl.textContent = 'URL belum tersedia, tunggu 5-10 detik...';
        }
      } else {
        dot.className = 'tunnel-status-dot off';
        statusText.textContent = 'Stopped';
        statusText.style.color = '#da3633';
        pidText.textContent = '';
        urlEl.textContent = '-';
      }
    } catch (e) {
      statusText.textContent = 'Error: ' + e.message;
      statusText.style.color = '#da3633';
    }
  }

  async function loadTunnelLog() {
    try {
      const res = await fetch('/api/tunnel/log');
      const data = await res.json();
      logEl.textContent = data.log || 'Belum ada log';
      logEl.scrollTop = logEl.scrollHeight;
    } catch (e) {
      logEl.textContent = 'Error: ' + e.message;
    }
  }

  document.getElementById('btnTunnelStart').addEventListener('click', async () => {
    Swal.fire({ title: 'Menjalankan tunnel...', didOpen: () => Swal.showLoading(), allowOutsideClick: false });
    try {
      const res = await fetch('/api/tunnel/start', { method: 'POST' });
      const data = await res.json();
      Swal.close();
      Swal.fire({ icon: 'success', title: 'Tunnel dimulai', text: data.msg, timer: 2500, showConfirmButton: false });
      setTimeout(() => { refreshTunnel(); loadTunnelLog(); }, 3000);
      setTimeout(() => { refreshTunnel(); }, 8000);
    } catch (e) {
      Swal.fire('Error', e.message, 'error');
    }
  });

  document.getElementById('btnTunnelStop').addEventListener('click', async () => {
    const r = await Swal.fire({
      title: 'Stop tunnel?', icon: 'warning',
      showCancelButton: true, confirmButtonText: 'Stop', confirmButtonColor: '#da3633',
    });
    if (!r.isConfirmed) return;
    try {
      const res = await fetch('/api/tunnel/stop', { method: 'POST' });
      const data = await res.json();
      Swal.fire({ icon: 'success', title: data.msg, timer: 1500, showConfirmButton: false });
      refreshTunnel();
    } catch (e) {
      Swal.fire('Error', e.message, 'error');
    }
  });

  document.getElementById('btnTunnelRefresh').addEventListener('click', () => {
    refreshTunnel();
    loadTunnelLog();
  });

  document.getElementById('btnTunnelCopy').addEventListener('click', () => {
    const url = urlEl.textContent.trim();
    if (!url || url === '-' || url.indexOf('http') === -1) {
      Swal.fire('Copy', 'URL belum tersedia', 'info');
      return;
    }
    const match = url.match(/https:\/\/[^\s]+/);
    const cleanUrl = match ? match[0] : url;
    navigator.clipboard.writeText(cleanUrl).then(() => {
      Swal.fire({ icon: 'success', title: 'URL dicopy', text: cleanUrl, timer: 1500, showConfirmButton: false });
    }).catch(() => {
      Swal.fire('Copy manual', cleanUrl, 'info');
    });
  });

  // Auto-refresh tiap 8 detik kalau panel terbuka
  setInterval(() => {
    if (panel.classList.contains('active')) {
      refreshTunnel();
    }
  }, 8000);
})();
"""
        content += js_extra
        js_file.write_text(content, encoding="utf-8")
        print(f"  OK  {js_file}")
    else:
        print("  SKIP  JS sudah ada")
else:
    print("  SKIP  dashboard.js tidak ada")

# ============================================================
# SELESAI
# ============================================================
print()
print("=" * 60)
print("  ✅ INSTALL BERHASIL")
print("=" * 60)
print()
print("  Langkah selanjutnya:")
print()
print("  1. Pastikan cloudflared terinstall:")
print("       pkg install -y cloudflared")
print("       cloudflared --version")
print()
print("  2. Restart server:")
print("       cd ~/capture-pro")
print("       python run.py")
print()
print("  3. Buka dashboard:")
print("       http://localhost:8000/dashboard")
print()
print("  4. Klik tombol hijau '🌐 Tunnel' di header")
print("     → klik '▶ Start' → tunggu 10 detik → URL muncul")
print()
print("  Backup file lama tersimpan sebagai *.bak2")
print()
