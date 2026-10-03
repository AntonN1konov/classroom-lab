"""
Classroom Lab — автономный запуск сервера.

Запускается из установленной программы (Windows / Linux):
  * хранит данные (база SQLite, экспорт, настройки) в папке пользователя;
  * при первом запуске генерирует секретный ключ для JWT;
  * поднимает сервер в локальной сети и открывает браузер;
  * показывает адрес, по которому подключаются студенты.
"""
import os
import secrets
import socket
import sys
import threading
import time
import traceback
import urllib.request
import webbrowser

APP_NAME = "Classroom Lab"
DEFAULT_PORT = 8000


def resource_dir() -> str:
    """Папка с файлами программы (внутри сборки PyInstaller или в репозитории)."""
    if getattr(sys, "frozen", False):
        return sys._MEIPASS  # type: ignore[attr-defined]
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def data_dir() -> str:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        path = os.path.join(base, "ClassroomLab")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")
        path = os.path.join(base, "classroom-lab")
    os.makedirs(path, exist_ok=True)
    return path


def read_env(path: str) -> dict:
    values = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    values[key.strip()] = value.strip()
    return values


def prepare_environment() -> None:
    root = resource_dir()
    data = data_dir()
    config_file = os.path.join(data, "config.env")

    config = read_env(config_file)
    if not config.get("SECRET_KEY"):
        with open(config_file, "a", encoding="utf-8") as f:
            f.write(f"SECRET_KEY={secrets.token_urlsafe(48)}\n")
        config = read_env(config_file)

    exports = os.path.join(data, "exports")
    os.makedirs(exports, exist_ok=True)

    os.environ.update(config)
    os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(data, "classroom.db").replace("\\", "/")
    os.environ["EXPORTS_DIR"] = exports
    os.environ["FRONTEND_DIST"] = os.path.join(root, "frontend_dist")
    os.environ["CLASSROOM_CONFIG_FILE"] = config_file

    backend = os.path.join(root, "backend")
    if os.path.isdir(backend) and backend not in sys.path:
        sys.path.insert(0, backend)


def local_ip() -> str:
    """IP-адрес компьютера в локальной сети (пакеты при этом не отправляются)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def free_port(start: int) -> int:
    for port in range(start, start + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    raise RuntimeError("Не удалось найти свободный порт")


def open_browser_when_ready(port: int) -> None:
    base = f"http://127.0.0.1:{port}"
    for _ in range(60):
        try:
            urllib.request.urlopen(f"{base}/api/health", timeout=1)
            break
        except Exception:
            time.sleep(0.5)
    # При первом запуске — выбор модели, дальше сразу вход
    configured = bool(os.getenv("LLM_PROVIDER") or os.getenv("YANDEXGPT_API_KEY"))
    webbrowser.open(f"{base}/login" if configured else f"{base}/setup")


def fix_console_encoding() -> None:
    """Вывод в файл или канал (не в консоль) не должен падать на кириллице."""
    for stream in (sys.stdout, sys.stderr):
        if stream and not stream.isatty() and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def main() -> None:
    fix_console_encoding()
    if sys.platform == "win32":
        os.system(f"title {APP_NAME}")

    prepare_environment()
    port = free_port(int(os.getenv("PORT", DEFAULT_PORT)))

    import uvicorn
    from app.main import app

    ip = local_ip()
    print("=" * 60)
    print(f"  {APP_NAME} запущен")
    print()
    print(f"  На этом компьютере:  http://localhost:{port}")
    print(f"  Для студентов:       http://{ip}:{port}")
    print()
    print("  Студенты должны быть в той же сети (Wi-Fi / LAN).")
    print(f"  Данные хранятся в:   {data_dir()}")
    print()
    print("  Чтобы остановить сервер, закройте это окно.")
    print("=" * 60)

    if os.getenv("CLASSROOM_NO_BROWSER") != "1":
        threading.Thread(target=open_browser_when_ready, args=(port,), daemon=True).start()

    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        if sys.stdin and sys.stdin.isatty():
            input("\nПроизошла ошибка. Нажмите Enter, чтобы закрыть окно...")
        sys.exit(1)
