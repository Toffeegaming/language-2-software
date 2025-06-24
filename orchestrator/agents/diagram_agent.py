from openai_manager import OpenAiManager
import requests

class DiagramAgent():
    def handle(self, request: str) -> str:
        url = "http://diagram-generator:8002/response"
        payload = {"message": request}
        try:
            resp = requests.post(url, params=payload)
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            return f"Error calling language-generator: {e}"
