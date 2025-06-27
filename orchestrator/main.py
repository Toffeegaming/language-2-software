from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import logfire
from pydantic_ai import Agent
import requests
from contextlib import asynccontextmanager
import pika
import threading
import asyncio

def call_language_agent(request: str) -> str:
    url = "http://language-agent:8011/run"
    payload = {"message": request}
    try:
        resp = requests.post(url, params=payload)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        return f"Error calling language-agent: {e}"

def call_diagram_agent(request: str) -> str:
    url = "http://diagram-agent:8012/run"
    payload = {"message": request}
    try:
        resp = requests.post(url, params=payload)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        return f"Error calling diagram-agent: {e}"

def call_software_agent(request: str) -> str:
    url = "http://software-agent:8013/run"
    payload = {"message": request}
    try:
        resp = requests.post(url, params=payload)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        return f"Error calling software-agent: {e}"

logfire.configure(token=os.getenv("LOGFIRE_WRITE_TOKEN"), service_name="orchestator")

class RabbitManager:
    def __init__(self, agent: Agent):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
        self.thread = None
        self.agent = agent

    def get_channel(self):
        return self.connection.channel()

    def start_in_background(self):
        self.thread = threading.Thread(target=self.setup_queue, daemon=True)
        self.thread.start()

    async def process_message(self, message):
        response = await self.agent.run(message)
        return response.output

    def setup_queue(self):
        channel = self.get_channel()
        channel.queue_declare(queue='orchestrator', durable=True)

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue='orchestrator', on_message_callback=self.on_request)

        print("Waiting RPC request on 'orchestrator' queue.")
        channel.start_consuming()

    def on_request(self, ch, method, properties, body):
        message = str(body)

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response = loop.run_until_complete(self.process_message(message))
        finally:
            loop.close()

        ch.basic_publish(exchange='',
                         routing_key=properties.reply_to,
                         body=response,
                         properties=pika.BasicProperties(
                             correlation_id=properties.correlation_id,
                             delivery_mode = pika.DeliveryMode.Persistent,
                         ))
        ch.basic_ack(delivery_tag=method.delivery_tag)

    def close(self):
        self.connection.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.agent = Agent(
        'gpt-4o-2024-05-13',
        deps_type=str,
        tools=[call_language_agent, call_diagram_agent, call_software_agent],
        system_prompt=(
            "You're an orchestrating agent. You use your tools to call other agents to generate text, diagrams, or software based on user requests. You do not generate text, diagrams, or software directly, but instead use your tools to call the agent services."
        ),
        instrument=True,
    )

    app.state.rabbit_manager = RabbitManager(app.state.agent)
    app.state.rabbit_manager.start_in_background()
    yield
    app.state.rabbit_manager.close()

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logfire.instrument_fastapi(app, capture_headers=True)

class QuestionModel(BaseModel):
    text: str

@app.head("/")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "ok"}

@app.post('/route')
async def route(request: Request, question: QuestionModel):
    """
    Expects a JSON body with a "question" field.
    Example:
    {
        "question": "Please create code for this... /Please create a diagram for this... /Please create a text for this..."
    }
    """

    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    agent = request.app.state.agent
    response = await agent.run(question.text)
    if response is None:
        raise HTTPException(status_code=500, detail="Internal Server Error")
    return response
