from openai_manager import OpenAiManager
import requests

class TextAgent():
    def handle(self, request: str) -> str:
        url = "http://language-generator:8001/response"
        payload = {"message": request}
        try:
            resp = requests.post(url, params=payload)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            return f"Error calling language-generator: {e}"