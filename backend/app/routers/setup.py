"""
Настройки подключения языковой модели (установленная версия).

Читать статус может любой. Менять настройки и проверять подключение — только
с компьютера, где запущен сервер (запросы с 127.0.0.1 / ::1), чтобы студенты
в локальной сети не могли подменить ключ или модель.
"""
import os
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.net import is_local_request
from app.services import llm, tunnel

router = APIRouter()


class SettingsRequest(BaseModel):
    provider: Literal["demo", "ollama", "openai", "yandexgpt"]
    folder_id: Optional[str] = None
    api_key: Optional[str] = None  # пусто — оставить сохранённый ключ
    ollama_url: Optional[str] = None
    ollama_model: Optional[str] = None
    openai_url: Optional[str] = None
    openai_model: Optional[str] = None  # пусто — первая загруженная модель


def _config_file() -> Optional[str]:
    return os.getenv("CLASSROOM_CONFIG_FILE")


def _is_local(request: Request) -> bool:
    return is_local_request(request)


def _require_local(request: Request) -> None:
    if not _config_file():
        raise HTTPException(status_code=404, detail="Настройка через интерфейс доступна только в установленной версии")
    if not _is_local(request):
        raise HTTPException(status_code=403, detail="Настройки можно менять только на компьютере, где запущен сервер")


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


def _resolve(data: SettingsRequest) -> dict:
    """Значения формы; пустые поля заменяются сохранёнными."""
    values = {"LLM_PROVIDER": data.provider}
    if data.provider == "yandexgpt":
        folder_id = (data.folder_id or os.getenv("YANDEX_CLOUD_FOLDER_ID") or "").strip()
        api_key = (data.api_key or os.getenv("YANDEXGPT_API_KEY") or "").strip()
        if not folder_id or not api_key:
            raise HTTPException(status_code=400, detail="Для YandexGPT нужны Folder ID и API-ключ")
        values.update(YANDEX_CLOUD_FOLDER_ID=folder_id, YANDEXGPT_API_KEY=api_key)
    elif data.provider == "ollama":
        values.update(
            OLLAMA_URL=(data.ollama_url or llm.DEFAULT_OLLAMA_URL).strip().rstrip("/"),
            OLLAMA_MODEL=(data.ollama_model or llm.DEFAULT_OLLAMA_MODEL).strip(),
        )
    elif data.provider == "openai":
        values.update(
            OPENAI_URL=(data.openai_url or llm.DEFAULT_OPENAI_URL).strip().rstrip("/"),
            OPENAI_MODEL=(data.openai_model or "").strip(),
        )
    return values


@router.get("/status")
async def setup_status(request: Request):
    local = _is_local(request)
    provider = llm.current_provider()
    status = {
        "provider": provider,
        "label": llm.provider_label(provider),
        "configured": provider != "demo",
        "first_run": not os.getenv("LLM_PROVIDER") and provider == "demo",
        "editable": bool(_config_file()) and local,
    }
    if local:
        status.update(
            folder_id=os.getenv("YANDEX_CLOUD_FOLDER_ID") or "",
            has_api_key=bool(os.getenv("YANDEXGPT_API_KEY")),
            ollama_url=os.getenv("OLLAMA_URL") or llm.DEFAULT_OLLAMA_URL,
            ollama_model=os.getenv("OLLAMA_MODEL") or llm.DEFAULT_OLLAMA_MODEL,
            openai_url=os.getenv("OPENAI_URL") or llm.DEFAULT_OPENAI_URL,
            openai_model=os.getenv("OPENAI_MODEL") or "",
        )
    return status


@router.post("/test")
def test_connection(data: SettingsRequest, request: Request):
    """Пробный запрос к модели с указанными (ещё не сохранёнными) настройками."""
    _require_local(request)
    values = _resolve(data)
    try:
        result = llm.send(
            "Ответь одним коротким предложением: ты на связи?",
            provider=data.provider,
            folder_id=values.get("YANDEX_CLOUD_FOLDER_ID"),
            api_key=values.get("YANDEXGPT_API_KEY"),
            ollama_url=values.get("OLLAMA_URL"),
            ollama_model=values.get("OLLAMA_MODEL"),
            openai_url=values.get("OPENAI_URL"),
            openai_model=values.get("OPENAI_MODEL"),
        )
    except llm.LLMError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return {"ok": True, "response": result["response"], "tokens_used": result["tokens_used"]}


@router.post("/")
async def save_setup(data: SettingsRequest, request: Request):
    _require_local(request)
    values = _resolve(data)
    _save_env(_config_file(), values)
    os.environ.update(values)
    return {"provider": data.provider, "label": llm.provider_label(data.provider)}


# --- Доступ из интернета и адреса для приглашений ---

def _port() -> int:
    return int(os.getenv("CLASSROOM_PORT") or os.getenv("PORT") or 8000)


@router.get("/addresses")
def server_addresses(request: Request):
    """Адреса, по которым студенты могут открыть сервер (для ссылок-приглашений)."""
    t = tunnel.status()
    return {
        "public_url": t["url"],
        "lan_url": os.getenv("CLASSROOM_LAN_URL"),
        "tunnel": {**t, "editable": _is_local(request)},
    }


@router.post("/tunnel/start")
def tunnel_start(request: Request):
    if not _is_local(request):
        raise HTTPException(status_code=403, detail="Доступ из интернета включается на компьютере, где запущен сервер")
    if not tunnel.binary():
        raise HTTPException(status_code=404, detail="Компонент cloudflared не найден. Переустановите программу.")
    result = tunnel.start(_port())
    if not result["running"]:
        raise HTTPException(status_code=502, detail=result["error"] or "Не удалось открыть доступ из интернета")
    return result


@router.post("/tunnel/stop")
def tunnel_stop(request: Request):
    if not _is_local(request):
        raise HTTPException(status_code=403, detail="Доступ из интернета выключается на компьютере, где запущен сервер")
    return tunnel.stop()
