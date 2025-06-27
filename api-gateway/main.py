from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import logfire
from contextlib import asynccontextmanager
import pika

logfire.configure(token=os.getenv("LOGFIRE_WRITE_TOKEN"), service_name="api-gateway")

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))

    yield

    app.state.connection.close()

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
        conn = request.app.state.connection
        channel = conn.channel()
        channel.queue_declare(queue='bff')
        channel.basic_publish(exchange='',
                              routing_key='orchestrator',
                              body='Hello orchestrator from your BFF the frontend!')
        return {"status": "Message sent to RabbitMQ successfully"}

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")
