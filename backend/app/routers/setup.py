"""
Первичная настройка автономной (desktop) сборки: ключ YandexGPT и Folder ID.

Изменять настройки можно только с того компьютера, где запущен сервер
(запросы с 127.0.0.1 / ::1), чтобы студенты в локальной сети не могли
подменить ключ.
"""
import os
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

router = APIRouter()

LOCAL_HOSTS = {"127.0.0.1", "::1", "localhost"}


class SetupRequest(BaseModel):
    folder_id: str = Field(min_length=1)
    api_key: str = Field(min_length=1)


def _config_file() -> Optional[str]:
    return os.getenv("CLASSROOM_CONFIG_FILE")


def _is_local(request: Request) -> bool:
    return request.client is not None and request.client.host in LOCAL_HOSTS


def _save_env(path: str, values: dict) -> None:
    lines = []
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            lines = [line.rstrip("\n") for line in f]
    keys_left = dict(values)
    result = []
    for line in lines:
        key = line.split("=", 1)[0].strip()
        if key in keys_left:
            result.append(f"{key}={keys_left.pop(key)}")
        else:
            result.append(line)
    result.extend(f"{k}={v}" for k, v in keys_left.items())
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(result) + "\n")


@router.get("/status")
async def setup_status(request: Request):
    return {
        "configured": bool(os.getenv("YANDEXGPT_API_KEY") and os.getenv("YANDEX_CLOUD_FOLDER_ID")),
        "editable": bool(_config_file()) and _is_local(request),
        "folder_id": os.getenv("YANDEX_CLOUD_FOLDER_ID") if _is_local(request) else None,
    }


@router.post("/")
async def save_setup(data: SetupRequest, request: Request):
    path = _config_file()
    if not path:
        raise HTTPException(status_code=404, detail="Настройка через интерфейс доступна только в установленной версии")
    if not _is_local(request):
        raise HTTPException(status_code=403, detail="Настройки можно менять только на компьютере, где запущен сервер")

    values = {
        "YANDEX_CLOUD_FOLDER_ID": data.folder_id.strip(),
        "YANDEXGPT_API_KEY": data.api_key.strip(),
    }
    _save_env(path, values)
    os.environ.update(values)
    return {"configured": True}
