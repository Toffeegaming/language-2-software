from openai import AsyncOpenAI

class OpenAiManager:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.available_models = []

    async def get_available_models(self):
        try:
            all_models=[]
            async for model in self.client.models.list():
                all_models.append(model.id)
            # Filter for chat/completion models if needed
            print(f"Available models: {all_models}")
            self.available_models = all_models
        except Exception as e:
            print(f"Error fetching models: {e}")
            self.available_models = []

    async def get_response(self, message: str, instructions: str = None):
        response = await self.client.responses.create(
            model=self.available_models[1],
            instructions="You are a coding assistant that talks like a pirate.",
            input=message,
        )
        return {"message": "Test successful", "response": response.output_text}
