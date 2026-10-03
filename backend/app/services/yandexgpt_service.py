import os
import json
import requests
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class YandexGPTService:
    def __init__(self):
        self.api_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    # Настройки читаются при каждом обращении, чтобы их можно было
    # задать после запуска (страница первичной настройки).
    @property
    def folder_id(self) -> Optional[str]:
        return os.getenv("YANDEX_CLOUD_FOLDER_ID")

    @property
    def api_key(self) -> Optional[str]:
        return os.getenv("YANDEXGPT_API_KEY")
        
    def _get_headers(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "Authorization": f"Api-Key {self.api_key}"
        }
    
    def _build_messages(self, prompt: str, context: Optional[List[Dict]] = None) -> List[Dict]:
        messages = []
        
        if context:
            messages.extend(context)
        
        messages.append({
            "role": "user",
            "text": prompt
        })
        
        return messages
    
    def send_request(
        self,
        prompt: str,
        context: Optional[List[Dict]] = None,
        model: str = "yandexgpt/latest"
    ) -> Dict:
        """
        Отправка запроса в YandexGPT API
        """
        if not self.api_key or not self.folder_id:
            raise ValueError("YandexGPT API ключ или Folder ID не настроены")
        
        messages = self._build_messages(prompt, context)
        
        payload = {
            "modelUri": f"gpt://{self.folder_id}/{model}",
            "completionOptions": {
                "stream": False,
                "temperature": 0.6,
                "maxTokens": "2000"
            },
            "messages": messages
        }
        
        try:
            response = requests.post(
                self.api_url,
                headers=self._get_headers(),
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            if "result" in result and "alternatives" in result["result"]:
                text = result["result"]["alternatives"][0]["message"]["text"]
                tokens_used = result.get("result", {}).get("usage", {}).get("totalTokens", 0)
                
                return {
                    "response": text,
                    "tokens_used": tokens_used,
                    "raw_response": result
                }
            else:
                raise ValueError(f"Неожиданный формат ответа от API: {result}")
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ошибка при обращении к YandexGPT API: {str(e)}")
    
    def format_context_from_messages(self, messages: List[Dict]) -> List[Dict]:
        """
        Форматирование сообщений для контекста YandexGPT
        """
        formatted = []
        for msg in messages:
            role = "assistant" if msg.get("is_from_yandexgpt") else "user"
            formatted.append({
                "role": role,
                "text": msg.get("content", "")
            })
        return formatted

