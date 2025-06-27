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
    def __init__(self, connection):
        self.connection = connection
        self.thread = None
        self.stop_event = threading.Event()

    def get_channel(self):
        return self.connection.channel()

    def start_in_background(self):
        self.thread = threading.Thread(target=self.setup_queue, daemon=True)
        self.thread.start()

    def setup_queue(self):
        channel = self.get_channel()
        channel.queue_declare(queue='bff')
        channel.basic_consume(queue='bff', on_message_callback=self.callback, auto_ack=True)
        print("Waiting for messages. To exit press CTRL+C")
        channel.start_consuming()
        # while not self.stop_event.is_set():
        #     try:
        #         channel.connection.process_data_events(time_limit=1)
        #     except Exception:
        #         break

    def callback(self, ch, method, properties, body):
        print(f"Received message: {body}")
        # Here you can add logic to process the message

    def close(self):
        self.stop_event.set()
        try:
            self.connection.close()
        except Exception:
            pass
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)

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

    app.state.rabbit_manager = RabbitManager(pika.BlockingConnection(pika.ConnectionParameters('rabbitmq')))
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

@app.get('/rabbitmq')
async def kut_konijn(request: Request):
    """
    Test RabbitMQ connection.
    """
    try:
        conn = request.app.state.connection
        channel = conn.channel()
        channel.queue_declare(queue='hello')
        channel.basic_publish(exchange='',
            routing_key='hello',
            body='Hello World!')

    except Exception as e:
        return f"Error connecting to RabbitMQ: {e}"