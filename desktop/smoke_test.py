"""
Проверка собранной программы: запускает исполняемый файл и проходит
основной сценарий через HTTP API (без обращения к YandexGPT).

    python desktop/smoke_test.py dist/ClassroomLab/ClassroomLab[.exe]
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

PORT = 8765
BASE = f"http://127.0.0.1:{PORT}"


def request(method, path, data=None, token=None, form=False):
    headers = {}
    body = None
    if data is not None:
        if form:
            body = "&".join(f"{k}={v}" for k, v in data.items()).encode()
            headers["Content-Type"] = "application/x-www-form-urlencoded"
        else:
            body = json.dumps(data).encode()
            headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(BASE + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            raw = r.read()
            ctype = r.headers.get("Content-Type", "")
            return r.status, (json.loads(raw) if "json" in ctype else raw.decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def check(cond, msg):
    print(("OK   " if cond else "FAIL ") + msg)
    if not cond:
        raise SystemExit(1)


def main():
    exe = os.path.abspath(sys.argv[1])
    home = tempfile.mkdtemp()
    env = dict(os.environ, PORT=str(PORT), CLASSROOM_NO_BROWSER="1",
               APPDATA=home, XDG_DATA_HOME=home)
    proc = subprocess.Popen([exe], env=env, stdin=subprocess.DEVNULL)
    try:
        for _ in range(120):
            try:
                if request("GET", "/api/health")[0] == 200:
                    break
            except Exception:
                pass
            if proc.poll() is not None:
                raise SystemExit(f"FAIL программа завершилась с кодом {proc.returncode}")
            time.sleep(0.5)
        else:
            raise SystemExit("FAIL сервер не запустился")

        check(request("GET", "/api/health")[0] == 200, "сервер отвечает")
        status, page = request("GET", "/login")
        check(status == 200 and "<div id=\"root\">" in page, "фронтенд раздаётся (/login)")
        status, data = request("GET", "/api/setup/status")
        check(status == 200 and data["configured"] is False and data["editable"] is True, "статус настройки")

        for user in (("teacher1", "teacher"), ("student1", "student")):
            status, _ = request("POST", "/api/auth/register", {
                "username": user[0], "email": f"{user[0]}@example.com",
                "full_name": user[0].title(), "password": "secret123", "role": user[1]})
            check(status == 200, f"регистрация {user[0]}")

        _, t = request("POST", "/api/auth/login", {"username": "teacher1", "password": "secret123"}, form=True)
        teacher = t["access_token"]
        _, me = request("GET", "/api/auth/me", token=teacher)
        _, s = request("POST", "/api/auth/login", {"username": "student1", "password": "secret123"}, form=True)
        _, student = request("GET", "/api/auth/me", token=s["access_token"])

        status, session = request("POST", "/api/sessions/", {"name": "Тестовая сессия", "description": "smoke"}, token=teacher)
        check(status == 200, "создание сессии")
        sid = session["id"]
        check(request("POST", f"/api/sessions/{sid}/students/{student['id']}", {}, token=teacher)[0] == 200,
              "добавление студента")
        check(request("POST", f"/api/sessions/{sid}/students/{me['id']}", {}, token=teacher)[0] == 400,
              "преподавателя нельзя добавить как студента")
        _, full = request("GET", f"/api/sessions/{sid}", token=teacher)
        check(len(full["students"]) == 1, "состав сессии")

        status, _ = request("POST", "/api/setup/", {"folder_id": "test-folder", "api_key": "test-key"})
        check(status == 200, "сохранение настроек YandexGPT")
        check(request("GET", "/api/setup/status")[1]["configured"] is True, "настройки применены без перезапуска")
        print("\nВсе проверки пройдены")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()
