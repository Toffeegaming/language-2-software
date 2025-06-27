from openai import AsyncOpenAI

class OpenAiManager:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.available_models = []
        self.prompt = """
        Generate the requested text as a plain string 
        with no extra formatting, code blocks, or JSON. Return only the text itself.
        """

    async def get_available_models(self):
        try:
            all_models=[]
            async for model in self.client.models.list():
                all_models.append(model.id)
            # Filter for chat/completion models if needed
            self.available_models = all_models
        except Exception as e:
            print(f"Error fetching models: {e}")
            self.available_models = []

    async def get_response(self, message: str, model: str = None):
        if not model:
            if not self.available_models:
                return {"error": "No available models found."}
            else:
                model = self.available_models[1]

        response = await self.client.responses.create(
            model=model,
            instructions=self.prompt,
            input=message,
        )
        return response.output_text

    async def get_streaming_response(self, message: str, model: str):
        if not model:
            if not self.available_models:
                yield {"error": "No available models found."}
            else:
                model = self.available_models[1]

        stream = await self.client.responses.create(
            model=model,
            instructions=self.prompt,
            input=message,
            stream=True,
        )

        async for event in stream:
            if event.type == "response.output_text.delta":
                yield event.delta
