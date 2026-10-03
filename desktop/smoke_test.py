"""
Проверка собранной программы: запускает исполняемый файл и проходит
основной сценарий через HTTP API (без обращения к YandexGPT).

    python desktop/smoke_test.py dist/ClassroomLab/ClassroomLab[.exe]
"""
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

PORT = 8765
BASE = f"http://127.0.0.1:{PORT}"
FAKE_LLM_PORT = 8766


class FakeLMStudio(BaseHTTPRequestHandler):
    """Имитация LM Studio: /v1/models и /v1/chat/completions."""

    def _send(self, data):
        body = json.dumps(data).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send({"data": [{"id": "qwen2.5-3b-instruct"}]})

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        last = req["messages"][-1]["content"]
        self._send({"choices": [{"message": {"role": "assistant",
                    "content": f"[{req['model']}] сообщений: {len(req['messages'])}; последнее: {last}"}}],
                    "usage": {"total_tokens": 42}})

    def log_message(self, *args):
        pass


def request(method, path, data=None, token=None, form=False, headers=None, base=None):
    headers = dict(headers or {})
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
    req = urllib.request.Request((base or BASE) + path, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
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
        check(status == 200 and data["provider"] == "demo" and data["first_run"] and data["editable"],
              "первый запуск: демо-режим, настройки доступны")

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

        # Демо-режим: преподаватель пишет напрямую (уровень 1)
        status, answer = request("POST", "/api/yandexgpt/send", {"prompt": "Привет", "session_id": sid}, token=teacher)
        check(status == 200 and "Демо-режим" in answer["response"], "ответ в демо-режиме")

        # Студент не может писать в модель напрямую, только через одобрение (уровень 2)
        stoken = s["access_token"]
        status, _ = request("POST", "/api/yandexgpt/send", {"prompt": "x", "session_id": sid}, token=stoken)
        check(status == 403, "студент не пишет в модель напрямую")
        status, pending = request("POST", "/api/chats/messages",
                                  {"content": "Вопрос студента", "chat_type": "yandexgpt", "session_id": sid}, token=stoken)
        check(status == 200 and pending["status"] == "pending", "промт студента ждёт одобрения")
        status, approved = request("POST", f"/api/yandexgpt/approve/{pending['id']}", {}, token=teacher)
        check(status == 200 and "№2" in approved["response"], "одобрение промта, общий контекст сессии")

        status, pdf = request("POST", "/api/export/session",
                              {"session_id": sid, "format": "pdf", "include_context": True}, token=teacher)
        check(status == 200 and str(pdf).startswith("%PDF"), "экспорт в PDF")

        # Ошибки подключения должны быть понятными, а не «500»
        status, err = request("POST", "/api/setup/test", {"provider": "ollama", "ollama_url": "http://127.0.0.1:9"})
        check(status == 502 and "Ollama" in err, "понятная ошибка, если Ollama не запущена")
        status, _ = request("POST", "/api/setup/", {"provider": "yandexgpt", "folder_id": "f"})
        check(status == 400, "YandexGPT без ключа не сохраняется")

        # LM Studio (OpenAI-совместимый сервер): проверка, сохранение, ответ в чате с контекстом
        fake = HTTPServer(("127.0.0.1", FAKE_LLM_PORT), FakeLMStudio)
        threading.Thread(target=fake.serve_forever, daemon=True).start()
        lm = {"provider": "openai", "openai_url": f"http://127.0.0.1:{FAKE_LLM_PORT}/v1"}
        status, data = request("POST", "/api/setup/test", lm)
        check(status == 200 and "qwen2.5-3b-instruct" in data["response"], "проверка подключения к LM Studio")
        check(request("POST", "/api/setup/", lm)[0] == 200, "сохранение LM Studio")
        status, answer = request("POST", "/api/yandexgpt/send", {"prompt": "Третий вопрос", "session_id": sid}, token=teacher)
        check(status == 200 and "сообщений: 5" in answer["response"] and answer["tokens_used"] == 42,
              "ответ локальной модели с историей сессии")
        fake.shutdown()
        fake.server_close()
        status, err = request("POST", "/api/yandexgpt/send", {"prompt": "x", "session_id": sid}, token=teacher)
        check(status == 502 and "LM Studio" in err, "понятная ошибка, если сервер LM Studio выключен")

        status, saved = request("POST", "/api/setup/", {"provider": "ollama", "ollama_model": "qwen2.5:0.5b"})
        check(status == 200, "сохранение настроек")
        _, data = request("GET", "/api/setup/status")
        check(data["provider"] == "ollama" and data["ollama_model"] == "qwen2.5:0.5b" and not data["first_run"],
              "настройки применены без перезапуска")

        # --- Запросы «из интернета» (через туннель/прокси) не считаются локальными ---
        remote = {"X-Forwarded-For": "203.0.113.7"}
        check(request("GET", "/api/auth/registration-options")[1]["can_register_teacher"] is True,
              "на компьютере с сервером можно создать преподавателя")
        check(request("GET", "/api/auth/registration-options", headers=remote)[1]["can_register_teacher"] is False,
              "из интернета нельзя создать преподавателя")
        status, _ = request("POST", "/api/auth/register", {"username": "hacker", "email": "h@example.com",
                            "full_name": "H", "password": "secret123", "role": "teacher"}, headers=remote)
        check(status == 403, "регистрация преподавателя из интернета запрещена")
        check(request("POST", "/api/setup/", {"provider": "demo"}, headers=remote)[0] == 403,
              "настройки из интернета менять нельзя")
        check(request("POST", "/api/setup/tunnel/start", headers=remote)[0] == 403,
              "туннель из интернета не включить")

        # --- Приглашение по ссылке ---
        status, inv = request("POST", f"/api/sessions/{sid}/invite", {}, token=teacher)
        check(status == 200 and inv["token"], "ссылка-приглашение создана")
        invite = inv["token"]
        check(request("POST", f"/api/sessions/{sid}/invite", {}, token=teacher)[1]["token"] == invite,
              "повторный запрос возвращает ту же ссылку")
        status, info = request("GET", f"/api/invites/{invite}", headers=remote)
        check(status == 200 and info["session_name"] == "Тестовая сессия", "страница приглашения доступна без входа")
        status, friend = request("POST", "/api/auth/register", {"username": "friend", "email": "friend@example.com",
                                 "full_name": "Друг", "password": "secret123"}, headers=remote)
        check(status == 200 and friend["role"] == "student", "друг регистрируется студентом")
        _, ft = request("POST", "/api/auth/login", {"username": "friend", "password": "secret123"}, form=True, headers=remote)
        status, joined = request("POST", f"/api/invites/{invite}/join", {}, token=ft["access_token"], headers=remote)
        check(status == 200 and joined["session_id"] == sid, "вступление в сессию по ссылке")
        _, sessions = request("GET", "/api/sessions/", token=ft["access_token"])
        check([x["id"] for x in sessions] == [sid], "сессия появилась у студента")
        status, msgs = request("GET", f"/api/chats/messages/{sid}?chat_type=group", token=ft["access_token"])
        check(status == 200, "студент читает групповой чат")
        check(request("POST", f"/api/invites/{invite}/join", {}, token=teacher)[0] == 400,
              "преподаватель не вступает по приглашению")
        new_invite = request("POST", f"/api/sessions/{sid}/invite/reset", {}, token=teacher)[1]["token"]
        check(new_invite != invite and request("GET", f"/api/invites/{invite}")[0] == 404,
              "после сброса старая ссылка не работает")

        # --- Доступ из интернета ---
        _, addr = request("GET", "/api/setup/addresses")
        check(addr["lan_url"] and addr["tunnel"]["available"], "адреса сервера и cloudflared в сборке")
        status, t = request("POST", "/api/setup/tunnel/start")
        if status == 200 and t.get("url"):
            print(f"OK   туннель открыт: {t['url']}")
            print(f"::notice title=Tunnel::opened {t['url']}")
            try:
                for _ in range(20):
                    try:
                        if request("GET", "/api/health", base=t["url"])[0] == 200:
                            break
                    except Exception:
                        time.sleep(2)
                status, _ = request("POST", "/api/setup/", {"provider": "demo"}, base=t["url"])
                check(status == 403, "через туннель настройки менять нельзя")
                status, info = request("GET", f"/api/invites/{new_invite}", base=t["url"])
                check(status == 200, "приглашение открывается через интернет")
            except SystemExit:
                raise
            except Exception as e:
                print(f"WARN туннель недоступен снаружи: {e}")
                print(f"::warning title=Tunnel::not reachable: {e}")
            request("POST", "/api/setup/tunnel/stop")
        else:
            print(f"WARN туннель не открылся (сеть CI?): {status} {t}")
            print(f"::warning title=Tunnel::not opened: {status}")
        print("\nВсе проверки пройдены")
        print("::notice title=Smoke test::all checks passed")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    main()
