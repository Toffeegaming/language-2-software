from ..openai_manager import OpenAiManager

class TextAgent():
    def handle(self, request: str) -> str:
        return "text generated for: " + request