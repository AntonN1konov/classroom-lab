"""Определение запросов «с этого компьютера»."""
from fastapi import Request

LOCAL_HOSTS = {"127.0.0.1", "::1", "localhost"}
# Заголовки, которые добавляют прокси и туннели (Cloudflare, nginx).
# Запрос через туннель приходит с 127.0.0.1, но сделан из интернета.
PROXY_HEADERS = ("x-forwarded-for", "cf-connecting-ip", "forwarded", "x-real-ip", "cf-ray")


def is_local_request(request: Request) -> bool:
    if request.client is None or request.client.host not in LOCAL_HOSTS:
        return False
    return not any(h in request.headers for h in PROXY_HEADERS)
