# ai_agent/grok_agent.py
import requests
from config import GROK_API_KEY

class GrokAgent:
    def __init__(self):
        self.api_url = "https://api.x.ai/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {GROK_API_KEY}",
            "Content-Type": "application/json"
        }
        self.model = "grok-beta"

    def ask(self, message: str, history: list = None) -> str:
        if history is None:
            history = []

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": message}],
            "temperature": 0.7,
            "max_tokens": 1024
        }

        try:
            response = requests.post(self.api_url, json=payload, headers=self.headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            return f"متأسفانه در حال حاضر هوش مصنوعی در دسترس نیست.\nلطفاً چند دقیقه دیگر تلاش کنید یا با پشتیبانی تماس بگیرید.\n\nخطا: {str(e)[:100]}"

# استفاده ساده:
# from ai_agent.grok_agent import GrokAgent
# agent = GrokAgent()
# reply = agent.ask("چطور در رویداد ثبت‌نام کنم؟")
