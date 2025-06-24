from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import os
from openai_manager import OpenAiManager

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
async def response(request: Request, message: str, model: str = None, instructions: str = None, stream: bool = False):
    oai_manager = request.app.state.oai_manager

    if stream:
        return StreamingResponse(oai_manager.get_streaming_response(message, model, instructions), media_type="text/plain")
    else:
        return  await oai_manager.get_response(message, model, instructions)
