"""
Доступ к серверу из интернета через Cloudflare Tunnel (quick tunnel).

cloudflared подключается к Cloudflare и получает адрес вида
https://<слова>.trycloudflare.com, который проксирует запросы на этот компьютер.
Не нужны ни белый IP, ни настройка роутера, ни аккаунт Cloudflare.
Адрес меняется при каждом запуске туннеля.
"""
import atexit
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from typing import Optional

URL_RE = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")

_lock = threading.Lock()
_proc: Optional[subprocess.Popen] = None
_url: Optional[str] = None
_error: Optional[str] = None


def binary() -> Optional[str]:
    path = os.getenv("CLOUDFLARED_PATH")
    if path and os.path.isfile(path):
        return path
    return shutil.which("cloudflared")


def status() -> dict:
    running = _proc is not None and _proc.poll() is None
    return {
        "available": binary() is not None,
        "running": running,
        "url": _url if running else None,
        "error": _error,
    }


def _read_output(proc: subprocess.Popen) -> None:
    global _url, _error
    for line in iter(proc.stdout.readline, ""):
        match = URL_RE.search(line)
        if match and not _url:
            _url = match.group(0)
    if _url is None:
        _error = "Туннель не запустился. Проверьте подключение к интернету и попробуйте ещё раз."


def start(port: int, timeout: float = 40) -> dict:
    global _proc, _url, _error
    with _lock:
        if _proc is not None and _proc.poll() is None:
            return status()
        exe = binary()
        if not exe:
            raise RuntimeError("cloudflared не найден")
        _url, _error = None, None
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        _proc = subprocess.Popen(
            [exe, "tunnel", "--no-autoupdate", "--url", f"http://127.0.0.1:{port}"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
            text=True, encoding="utf-8", errors="replace", creationflags=flags,
        )
        threading.Thread(target=_read_output, args=(_proc,), daemon=True).start()

    deadline = time.time() + timeout
    while time.time() < deadline and _url is None and _proc.poll() is None:
        time.sleep(0.3)
    if _url is None:
        stop()
        _error = _error or "Не удалось получить адрес туннеля за отведённое время."
    return status()


def stop() -> dict:
    global _proc, _url
    with _lock:
        if _proc is not None and _proc.poll() is None:
            _proc.terminate()
            try:
                _proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                _proc.kill()
        _proc, _url = None, None
    return status()


atexit.register(stop)
