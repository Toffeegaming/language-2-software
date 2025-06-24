from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
from openai import AsyncOpenAI
import os

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

    async def get_response(self, message: str):
        response = await self.client.responses.create(
            model=self.available_models[0],
            instructions="You are a coding assistant that talks like a pirate.",
            input=message,
        )

        return {"message": "Test successful", "response": response.output_text}

@asynccontextmanager
async def lifespan(app: FastAPI):
    oai_manager = OpenAiManager(api_key=os.getenv("OPENAI_API_KEY"))
    await oai_manager.get_available_models()

    app.state.oai_manager = oai_manager

    yield

app = FastAPI(lifespan=lifespan)

@app.head("/")
async def health_check():
    return {"status": "ok"}

@app.get("/models")
async def get_models(request: Request):
    oai_manager = request.app.state.oai_manager
    return {"available_models": oai_manager.available_models}

@app.post("/response")
async def test(request: Request, message: str):
    return await request.app.state.oai_manager.get_response(message)


# streaming
# async def main():
#     stream = await client.responses.create(
#         model="gpt-4o",
#         input="Write a one-sentence bedtime story about a unicorn.",
#         stream=True,
#     )
#
#     async for event in stream:
#         print(event)
#
#
# asyncio.run(main())