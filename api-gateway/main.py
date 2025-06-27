from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import logfire
from contextlib import asynccontextmanager
import pika
import uuid

logfire.configure(token=os.getenv("LOGFIRE_WRITE_TOKEN"), service_name="api-gateway")

class RabbitManager:
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue='', exclusive=True, durable=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True
        )

        self.response = None
        self.corr_id = None

    def on_response(self, ch, method, properties, body):
        if self.corr_id == properties.correlation_id:
            self.response = body

    def call(self, message: str):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key='orchestrator',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
                delivery_mode = pika.DeliveryMode.Persistent
            ),
            body=message
        )

        while self.response is None:
            self.connection.process_data_events(time_limit=60)
        return self.response

    def close(self):
        self.connection.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.rabbit_manager = RabbitManager()
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
    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    try:
        response = request.app.state.rabbit_manager.call(question.text)
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
