"""
Подключение языковой модели.

Провайдер выбирается переменной LLM_PROVIDER:
  * demo      — без модели, бесплатно: проверка интерфейса и сценариев;
  * ollama    — локальная модель через Ollama (https://ollama.com), бесплатно;
  * openai    — OpenAI-совместимый сервер: LM Studio (https://lmstudio.ai), vLLM и др.;
  * yandexgpt — YandexGPT в Yandex Cloud (платно, нужен API-ключ).

Если LLM_PROVIDER не задан: yandexgpt при наличии ключа, иначе demo.
"""
import os
from typing import Dict, List, Optional

import requests


class LLMError(Exception):
    """Ошибка, текст которой можно показать пользователю."""


PROVIDERS = ("demo", "ollama", "openai", "yandexgpt")
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_OLLAMA_MODEL = "qwen2.5:3b"
DEFAULT_OPENAI_URL = "http://127.0.0.1:1234/v1"  # LM Studio


def current_provider() -> str:
    provider = (os.getenv("LLM_PROVIDER") or "").strip().lower()
    if provider in PROVIDERS:
        return provider
    if os.getenv("YANDEXGPT_API_KEY") and os.getenv("YANDEX_CLOUD_FOLDER_ID"):
        return "yandexgpt"
    return "demo"


def provider_label(provider: Optional[str] = None) -> str:
    provider = provider or current_provider()
    if provider == "ollama":
        return f"Локальная модель ({os.getenv('OLLAMA_MODEL') or DEFAULT_OLLAMA_MODEL})"
    if provider == "openai":
        model = os.getenv("OPENAI_MODEL")
        return f"Локальная модель ({model})" if model else "Локальная модель (LM Studio)"
    if provider == "yandexgpt":
        return "YandexGPT"
    return "Демо-режим"


def _demo(prompt: str, context: Optional[List[Dict]]) -> Dict:
    turns = len([m for m in (context or []) if m.get("role") == "user"]) + 1
    text = (
        "Демо-режим: языковая модель не подключена, поэтому это тестовый ответ.\n\n"
        f"Ваш запрос №{turns} в этой сессии: «{prompt}»\n\n"
        "Чтобы получать настоящие ответы, преподаватель может подключить "
        "YandexGPT или бесплатную локальную модель в разделе «Настройки ИИ»."
    )
    return {"response": text, "tokens_used": 0}


def _ollama(prompt: str, context: Optional[List[Dict]], url: Optional[str] = None,
            model: Optional[str] = None) -> Dict:
    url = (url or os.getenv("OLLAMA_URL") or DEFAULT_OLLAMA_URL).rstrip("/")
    model = model or os.getenv("OLLAMA_MODEL") or DEFAULT_OLLAMA_MODEL
    messages = [{"role": m["role"], "content": m["text"]} for m in (context or [])]
    messages.append({"role": "user", "content": prompt})
    try:
        r = requests.post(f"{url}/api/chat", json={"model": model, "messages": messages, "stream": False},
                          timeout=300)
    except requests.exceptions.ConnectionError:
        raise LLMError(f"Ollama не запущена или недоступна по адресу {url}. "
                       "Установите Ollama с ollama.com и запустите её.")
    except requests.exceptions.Timeout:
        raise LLMError("Локальная модель не ответила за 5 минут. Попробуйте модель поменьше.")
    if r.status_code == 404:
        raise LLMError(f"Модель «{model}» не найдена в Ollama. Скачайте её командой: ollama pull {model}")
    if not r.ok:
        raise LLMError(f"Ollama вернула ошибку {r.status_code}: {r.text[:300]}")
    data = r.json()
    return {
        "response": data.get("message", {}).get("content", ""),
        "tokens_used": int(data.get("prompt_eval_count") or 0) + int(data.get("eval_count") or 0),
    }


def _openai_compatible(prompt: str, context: Optional[List[Dict]], url: Optional[str] = None,
                      model: Optional[str] = None) -> Dict:
    """LM Studio и другие серверы с API в формате OpenAI (/v1/chat/completions)."""
    url = (url or os.getenv("OPENAI_URL") or DEFAULT_OPENAI_URL).rstrip("/")
    model = model or os.getenv("OPENAI_MODEL") or ""
    headers = {}
    if os.getenv("OPENAI_API_KEY"):
        headers["Authorization"] = f"Bearer {os.getenv('OPENAI_API_KEY')}"
    try:
        if not model:
            # Модель не указана — берём первую загруженную в LM Studio
            r = requests.get(f"{url}/models", headers=headers, timeout=10)
            models = r.json().get("data", []) if r.ok else []
            if not models:
                raise LLMError("В LM Studio не загружена ни одна модель. Загрузите модель на вкладке Developer.")
            model = models[0]["id"]
        messages = [{"role": m["role"], "content": m["text"]} for m in (context or [])]
        messages.append({"role": "user", "content": prompt})
        r = requests.post(f"{url}/chat/completions", headers=headers,
                          json={"model": model, "messages": messages, "temperature": 0.6, "stream": False},
                          timeout=300)
    except requests.exceptions.ConnectionError:
        raise LLMError(f"Сервер модели недоступен по адресу {url}. В LM Studio откройте вкладку Developer "
                       "и включите сервер (Status: Running).")
    except requests.exceptions.Timeout:
        raise LLMError("Локальная модель не ответила за 5 минут. Попробуйте модель поменьше.")
    if not r.ok:
        raise LLMError(f"Сервер модели вернул ошибку {r.status_code}: {r.text[:300]}")
    data = r.json()
    try:
        text = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise LLMError(f"Неожиданный ответ сервера модели: {str(data)[:300]}")
    return {"response": text, "tokens_used": int((data.get("usage") or {}).get("total_tokens") or 0)}


def _yandexgpt(prompt: str, context: Optional[List[Dict]], folder_id: Optional[str] = None,
               api_key: Optional[str] = None) -> Dict:
    folder_id = folder_id or os.getenv("YANDEX_CLOUD_FOLDER_ID")
    api_key = api_key or os.getenv("YANDEXGPT_API_KEY")
    if not folder_id or not api_key:
        raise LLMError("YandexGPT не настроен: укажите Folder ID и API-ключ в разделе «Настройки ИИ».")
    messages = list(context or []) + [{"role": "user", "text": prompt}]
    payload = {
        "modelUri": f"gpt://{folder_id}/yandexgpt/latest",
        "completionOptions": {"stream": False, "temperature": 0.6, "maxTokens": "2000"},
        "messages": messages,
    }
    try:
        r = requests.post(
            "https://llm.api.cloud.yandex.net/foundationModels/v1/completion",
            headers={"Authorization": f"Api-Key {api_key}", "x-folder-id": folder_id},
            json=payload, timeout=60,
        )
    except requests.exceptions.RequestException as e:
        raise LLMError(f"Нет связи с Yandex Cloud: {e}")

    if not r.ok:
        try:
            detail = r.json().get("error", {}).get("message") or r.json().get("message") or r.text
        except ValueError:
            detail = r.text
        hints = {
            400: "Проверьте Folder ID: он должен быть от каталога, где создан сервисный аккаунт.",
            401: "API-ключ не принят. Проверьте, что он скопирован целиком.",
            402: "Проверьте платёжный аккаунт в Yandex Cloud: он должен быть активен.",
            403: "Нет прав: выдайте сервисному аккаунту роль ai.languageModels.user "
                 "и создайте ключ с областью yc.ai.languageModels.execute.",
            429: "Превышен лимит запросов. Подождите немного и повторите.",
        }
        hint = hints.get(r.status_code, "")
        raise LLMError(f"YandexGPT вернул ошибку {r.status_code}. {hint} Ответ сервера: {str(detail)[:300]}")

    result = r.json().get("result", {})
    try:
        text = result["alternatives"][0]["message"]["text"]
    except (KeyError, IndexError):
        raise LLMError(f"Неожиданный ответ YandexGPT: {str(result)[:300]}")
    return {"response": text, "tokens_used": int(result.get("usage", {}).get("totalTokens") or 0)}


def send(prompt: str, context: Optional[List[Dict]] = None, provider: Optional[str] = None, **options) -> Dict:
    """
    Отправить запрос модели. context — список {"role": "user"|"assistant", "text": ...}.
    Возвращает {"response": str, "tokens_used": int}.
    """
    provider = provider or current_provider()
    if provider == "ollama":
        return _ollama(prompt, context, options.get("ollama_url"), options.get("ollama_model"))
    if provider == "openai":
        return _openai_compatible(prompt, context, options.get("openai_url"), options.get("openai_model"))
    if provider == "yandexgpt":
        return _yandexgpt(prompt, context, options.get("folder_id"), options.get("api_key"))
    return _demo(prompt, context)
