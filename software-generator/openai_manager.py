from openai import AsyncOpenAI

class OpenAiManager:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.available_models = []
        self.prompt = """
        Write the complete source code for the requested software.

        Only output a markdown code block with the language specified (e.g., ```python). 
        Do not include any explanations, comments, strings, or formatting outside the code block.
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
                model = self.available_models[1] # use the first available model, which is codex-mini-latest

        response = await self.client.responses.create(
            model=model,
            instructions=self.prompt,
            input=message,
        )

        print(f"Response: {response.output_text}")

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
