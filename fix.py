"""Patch setup_full.py — ganti triple-double-quote README jadi triple-single."""
from pathlib import Path

p = Path("setup_full.py")
src = p.read_text(encoding="utf-8")

# Cari blok README
start_marker = 'F["README.md"] = """'
end_marker = '"""\n\nF["Makefile"]'

if start_marker not in src:
    print("❌ Marker start tidak ketemu. Cek manual.")
    raise SystemExit(1)

start = src.index(start_marker)
# cari penutup setelah start
end = src.index(end_marker, start)

# Ambil isi README (tanpa marker pembuka)
readme_content = src[start + len(start_marker):end]

# Ganti jadi triple-single-quote
new_block = "F[\"README.md\"] = '''" + readme_content + "'''\n\nF[\"Makefile\"]"

new_src = src[:start] + new_block + src[end + len(end_marker):]
p.write_text(new_src, encoding="utf-8")
print("✅ Fixed! Coba jalankan: python setup_full.py")
