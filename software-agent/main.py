from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import os
import logfire
from pydantic_ai import Agent
import requests

def call_code_generator(request: str) -> str:
    url = "http://software-generator:8003/response"
    payload = {"message": request}
    try:
        resp = requests.post(url, params=payload)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        return f"Error calling software-generator: {e}"

logfire.configure(token=os.getenv("LOGFIRE_WRITE_TOKEN"), service_name="software-agent")

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.agent = Agent(
        'gpt-4o-2024-05-13',
        deps_type=str,
        tools=[call_code_generator],
        system_prompt=(
            "You're a software agent. You generate code based on user requests. Use your different tools to create code in the requested format and language."
        ),
        instrument=True,
    )

    yield

app = FastAPI(lifespan=lifespan)
logfire.instrument_fastapi(app, capture_headers=True)

@app.head("/")
async def health_check():
    return {"status": "ok"}

@app.post("/run")
async def run_agent(request: Request, message: str):
    agent = request.app.state.agent
    response = await agent.run(message)
    return response.output
