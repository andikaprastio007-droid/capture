"""Web Code Editor — read/write file project dari dashboard."""
import os
import shutil
import subprocess
import platform
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path.home() / "capture-pro"

BLOCKED = [".git", "__pycache__", "venv", "data", "tunnel.log", "tunnel.pid"]
ALLOWED_EXT = [
    ".py", ".html", ".css", ".js", ".json", ".txt", ".md",
    ".env", ".example", ".conf", ".sh", ".xml", ".yml", ".yaml",
    ".sql", ".ini", ".cfg",
]


def _is_safe_path(rel_path):
    try:
        full = (PROJECT_ROOT / rel_path).resolve()
        if not str(full).startswith(str(PROJECT_ROOT.resolve())):
            return False, None
        return True, full
    except Exception:
        return False, None


def list_files():
    files = []
    for root, dirs, filenames in os.walk(PROJECT_ROOT):
        dirs[:] = [d for d in dirs if d not in BLOCKED and not d.startswith(".")]
        for f in filenames:
            full = Path(root) / f
            rel = full.relative_to(PROJECT_ROOT)
            ext = full.suffix.lower()
            size = full.stat().st_size
            files.append({
                "path": str(rel),
                "name": f,
                "ext": ext,
                "size": size,
                "size_human": _human_size(size),
                "editable": ext in ALLOWED_EXT,
                "dir": str(Path(root).relative_to(PROJECT_ROOT)) or ".",
            })
    files.sort(key=lambda x: x["path"])
    return files


def _human_size(n):
    for unit in ["B", "KB", "MB", "GB"]:
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def read_file(rel_path):
    safe, full = _is_safe_path(rel_path)
    if not safe:
        return {"ok": False, "msg": "Path tidak valid"}
    if not full.exists():
        return {"ok": False, "msg": "File tidak ada"}
    if not full.is_file():
        return {"ok": False, "msg": "Bukan file"}
    ext = full.suffix.lower()
    if ext not in ALLOWED_EXT:
        return {"ok": False, "msg": f"Ekstensi {ext} tidak bisa diedit"}
    try:
        content = full.read_text(encoding="utf-8", errors="replace")
        return {
            "ok": True,
            "path": rel_path,
            "content": content,
            "size": len(content),
            "ext": ext.lstrip("."),
            "modified": datetime.fromtimestamp(full.stat().st_mtime).isoformat(),
        }
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def write_file(rel_path, content, backup=True):
    safe, full = _is_safe_path(rel_path)
    if not safe:
        return {"ok": False, "msg": "Path tidak valid"}
    if not full.parent.exists():
        return {"ok": False, "msg": "Folder tidak ada"}
    ext = full.suffix.lower()
    if ext not in ALLOWED_EXT:
        return {"ok": False, "msg": f"Ekstensi {ext} tidak bisa diedit"}

    backup_path = None
    if backup and full.exists():
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = full.with_suffix(full.suffix + f".bak.{ts}")
        try:
            shutil.copy2(full, backup_path)
        except Exception as e:
            print(f"[backup] {e}")

    try:
        full.write_text(content, encoding="utf-8")
        return {
            "ok": True,
            "msg": "Tersimpan",
            "path": rel_path,
            "backup": str(backup_path.name) if backup_path else None,
            "size": len(content),
        }
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def delete_file(rel_path):
    safe, full = _is_safe_path(rel_path)
    if not safe:
        return {"ok": False, "msg": "Path tidak valid"}
    if not full.exists():
        return {"ok": False, "msg": "File tidak ada"}

    trash = PROJECT_ROOT / ".trash"
    trash.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = trash / (full.name + f".{ts}")
    try:
        shutil.move(str(full), str(dest))
        return {"ok": True, "msg": f"Dipindah ke .trash/{dest.name}"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def run_command(cmd, timeout=30):
    allowed = [
        "python run.py", "python worker.py",
        "python -m", "pip install", "pip list", "pip show",
        "ls", "pwd", "cat", "grep", "wc", "head", "tail",
        "pgrep", "pkill -f python run.py",
        "./tunnel_service.sh", "bash -c", "python3 -c",
    ]
    cmd_lower = cmd.strip().lower()
    is_allowed = any(cmd_lower.startswith(a.lower()) for a in allowed)
    if not is_allowed:
        return {"ok": False, "msg": f"Command tidak diizinkan. Contoh: ls, cat, python run.py"}
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                                timeout=timeout, cwd=str(PROJECT_ROOT))
        return {"ok": True, "stdout": result.stdout, "stderr": result.stderr, "code": result.returncode}
    except subprocess.TimeoutExpired:
        return {"ok": False, "msg": "Timeout"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def restart_server():
    """Restart Flask server — DETACHED via setsid + start_new_session."""
    script = PROJECT_ROOT / "start.sh"
    if not script.exists():
        return {"ok": False, "msg": "start.sh tidak ada"}
    
    try:
        # Cek apakah setsid tersedia
        import shutil as _sh
        if _sh.which("setsid"):
            cmd = ["setsid", "bash", str(script)]
        else:
            cmd = ["nohup", "bash", str(script)]
        
        # start_new_session=True → child lepas dari parent (Flask)
        # close_fds=True → tidak share file descriptor
        # stdin/stdout/stderr = DEVNULL → tidak terkait terminal
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            cwd=str(PROJECT_ROOT),
            start_new_session=True,
            close_fds=True,
        )
        return {
            "ok": True,
            "msg": "Server akan restart di background. Tunggu 5 detik, lalu refresh browser.",
            "pid": proc.pid,
        }
    except Exception as e:
        return {"ok": False, "msg": str(e)}



def search_files(query, ext_filter=None):
    results = []
    query_lower = query.lower()
    for f in list_files():
        if not f["editable"]:
            continue
        if ext_filter and f["ext"] != ext_filter:
            continue
        try:
            full = PROJECT_ROOT / f["path"]
            content = full.read_text(encoding="utf-8", errors="ignore")
            for i, line in enumerate(content.split("\n"), 1):
                if query_lower in line.lower():
                    results.append({"file": f["path"], "line": i, "text": line.strip()[:200]})
                    if len(results) >= 100:
                        return results
        except Exception:
            continue
    return results
