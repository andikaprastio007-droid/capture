"""Tunnel Manager API — kelola multiple tunnel."""
from flask import Blueprint, jsonify, request
from app.auth import login_required
import subprocess
import os

bp = Blueprint("tunnels", __name__)

PROJECT = os.path.expanduser("~/capture-pro")
SCRIPT = os.path.join(PROJECT, "multi_tunnel.sh")
TUNNEL_DIR = os.path.join(PROJECT, "tunnels")


def _run(args, timeout=60):
    """Jalankan multi_tunnel.sh."""
    if not os.path.isfile(SCRIPT):
        return {"ok": False, "msg": "multi_tunnel.sh tidak ada"}
    
    try:
        result = subprocess.run(
            ["bash", SCRIPT] + args,
            capture_output=True, text=True, timeout=timeout,
            cwd=PROJECT,
        )
        return {
            "ok": True,
            "stdout": result.stdout or "",
            "stderr": result.stderr or "",
            "code": result.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "msg": "Timeout"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


@bp.route("/tunnel-manager")
@login_required
def tunnel_manager_page():
    from flask import render_template
    return render_template("tunnels.html")


@bp.route("/tunnels/list")
@login_required
def list_tunnels():
    """List semua tunnel aktif."""
    tunnels = []
    
    if not os.path.isdir(TUNNEL_DIR):
        return jsonify({"ok": True, "tunnels": []})
    
    for filename in os.listdir(TUNNEL_DIR):
        if not filename.endswith(".pid"):
            continue
        
        name = filename[:-4]
        pid_file = os.path.join(TUNNEL_DIR, filename)
        url_file = os.path.join(TUNNEL_DIR, name + ".url")
        log_file = os.path.join(TUNNEL_DIR, name + ".log")
        
        try:
            with open(pid_file) as f:
                pid = int(f.read().strip())
        except Exception:
            continue
        
        # Cek PID hidup (Android blokir kill -0, pakai ps)
        running = False
        try:
            result = subprocess.run(["ps", "-p", str(pid)], capture_output=True, text=True, timeout=3)
            running = str(pid) in result.stdout
        except Exception:
            running = False
        
        # URL
        url = ""
        if os.path.isfile(url_file):
            try:
                with open(url_file) as f:
                    url = f.read().strip()
            except Exception:
                pass
        
        # Provider (dari log)
        provider = "unknown"
        if os.path.isfile(log_file):
            try:
                with open(log_file) as f:
                    log_content = f.read()[:500]
                if "cloudflared" in log_content:
                    provider = "cloudflare"
                elif "localhost.run" in log_content or "lhr.life" in log_content:
                    provider = "localhost.run"
                elif "serveo" in log_content:
                    provider = "serveo"
            except Exception:
                pass
        
        tunnels.append({
            "name": name,
            "pid": pid,
            "running": running,
            "url": url,
            "provider": provider,
        })
    
    # Sort: main first, backup second
    def sort_key(t):
        name = t["name"]
        if name == "main" or name == "primary":
            return 0
        if name == "backup":
            return 1
        return 2
    
    tunnels.sort(key=sort_key)
    
    return jsonify({"ok": True, "tunnels": tunnels})


@bp.route("/tunnels/start", methods=["POST"])
@login_required
def start_tunnel():
    """Start tunnel baru."""
    data = request.get_json(force=True, silent=True) or {}
    name = (data.get("name") or "").strip()
    provider = (data.get("provider") or "cloudflare").strip()
    port = str(data.get("port") or "8000").strip()
    
    if not name:
        return jsonify({"ok": False, "msg": "Nama tunnel kosong"}), 400
    
    if provider not in ("cloudflare", "localhost.run", "serveo"):
        return jsonify({"ok": False, "msg": "Provider tidak valid"}), 400
    
    result = _run(["start", name, provider, port], timeout=45)
    return jsonify(result)


@bp.route("/tunnels/stop", methods=["POST"])
@login_required
def stop_tunnel():
    """Stop tunnel."""
    data = request.get_json(force=True, silent=True) or {}
    name = (data.get("name") or "").strip()
    
    if not name:
        return jsonify({"ok": False, "msg": "Nama kosong"}), 400
    
    result = _run(["stop", name], timeout=15)
    return jsonify(result)


@bp.route("/tunnels/url/<name>")
@login_required
def tunnel_url(name):
    """Get URL tunnel."""
    url_file = os.path.join(TUNNEL_DIR, name + ".url")
    if not os.path.isfile(url_file):
        return jsonify({"ok": False, "msg": "Tunnel tidak ada"}), 404
    
    try:
        with open(url_file) as f:
            url = f.read().strip()
        return jsonify({"ok": True, "url": url})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500


@bp.route("/tunnels/log/<name>")
@login_required
def tunnel_log(name):
    """Get tunnel log."""
    log_file = os.path.join(TUNNEL_DIR, name + ".log")
    if not os.path.isfile(log_file):
        return jsonify({"ok": False, "msg": "Log tidak ada"}), 404
    
    try:
        with open(log_file) as f:
            lines = f.readlines()[-50:]
        return jsonify({"ok": True, "log": "".join(lines)})
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500


@bp.route("/tunnels/failover", methods=["POST"])
@login_required
def failover():
    """Set webhook ke tunnel primary."""
    script = os.path.join(PROJECT, "failover_webhook.sh")
    if not os.path.isfile(script):
        return jsonify({"ok": False, "msg": "failover_webhook.sh tidak ada"}), 404
    
    try:
        result = subprocess.run(
            ["bash", script],
            capture_output=True, text=True, timeout=30,
            cwd=PROJECT,
        )
        return jsonify({
            "ok": True,
            "msg": result.stdout.strip() or "Webhook updated",
        })
    except Exception as e:
        return jsonify({"ok": False, "msg": str(e)}), 500


@bp.route("/tunnels/start-dual", methods=["POST"])
@login_required
def start_dual():
    """Start 2 tunnel sekaligus (primary + backup)."""
    results = []
    
    # Primary: Cloudflare
    r1 = _run(["start", "main", "cloudflare", "8000"], timeout=45)
    results.append({"name": "main", "result": r1})
    
    # Backup: localhost.run
    r2 = _run(["start", "backup", "localhost.run", "8000"], timeout=45)
    results.append({"name": "backup", "result": r2})
    
    # Set webhook
    try:
        subprocess.run(["bash", os.path.join(PROJECT, "failover_webhook.sh")],
                       capture_output=True, timeout=20)
    except Exception:
        pass
    
    return jsonify({"ok": True, "results": results})


@bp.route("/tunnels/stop-all", methods=["POST"])
@login_required
def stop_all():
    """Stop semua tunnel."""
    results = []
    
    if os.path.isdir(TUNNEL_DIR):
        for filename in os.listdir(TUNNEL_DIR):
            if filename.endswith(".pid"):
                name = filename[:-4]
                r = _run(["stop", name], timeout=15)
                results.append({"name": name, "result": r})
    
    return jsonify({"ok": True, "results": results})

@bp.route("/tunnels/public/list")
def public_list():
    """Debug endpoint — tanpa login."""
    import os
    tunnels = []
    TUNNEL_DIR = os.path.expanduser("~/capture-pro/tunnels")
    if os.path.isdir(TUNNEL_DIR):
        for f in os.listdir(TUNNEL_DIR):
            if f.endswith(".pid"):
                name = f[:-4]
                try:
                    pid = int(open(os.path.join(TUNNEL_DIR, f)).read().strip())
                except:
                    continue
                url = ""
                url_file = os.path.join(TUNNEL_DIR, name + ".url")
                if os.path.isfile(url_file):
                    url = open(url_file).read().strip()
                tunnels.append({"name": name, "pid": pid, "url": url})
    return jsonify({"ok": True, "tunnels": tunnels, "debug": True})
