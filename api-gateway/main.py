from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import logfire
from contextlib import asynccontextmanager
import pika
import uuid
import threading
import time

logfire.configure(token=os.getenv("LOGFIRE_WRITE_TOKEN"), service_name="api-gateway")

class RabbitManager:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.callback_queue = None
        self.response = None
        self.corr_id = None
        self._lock = threading.Lock()
        self._connected = threading.Event()
        self._closing = False
        self._consumer_tag = None
        self._start_connection_thread()

    def _start_connection_thread(self):
        t = threading.Thread(target=self._run, daemon=True)
        t.start()

    def _run(self):
        while not self._closing:
            try:
                self._connect()
                self._connected.set()
                self.connection.ioloop.start()
            except Exception as e:
                print(f"RabbitMQ connection error: {e}, retrying in 5s...")
                self._connected.clear()
                time.sleep(5)

    def _connect(self):
        params = pika.ConnectionParameters('rabbitmq')
        self.connection = pika.SelectConnection(
            parameters=params,
            on_open_callback=self.on_connection_open,
            on_open_error_callback=self.on_connection_open_error,
            on_close_callback=self.on_connection_closed
        )

    def on_connection_open(self, connection):
        connection.channel(on_open_callback=self.on_channel_open)

    def on_connection_open_error(self, connection, exc):
        print(f"Connection open failed: {exc}")
        self.connection.ioloop.stop()

    def on_connection_closed(self, connection, reason):
        print(f"Connection closed: {reason}")
        self._connected.clear()
        if not self._closing:
            self.connection.ioloop.stop()

    def on_channel_open(self, channel):
        self.channel = channel
        self.channel.queue_declare('', exclusive=True, durable=True, callback=self.on_queue_declared)

    def on_queue_declared(self, method_frame):
        self.callback_queue = method_frame.method.queue
        self._consumer_tag = self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True
        )

    def on_response(self, ch, method, properties, body):
        if self.corr_id == properties.correlation_id:
            self.response = body

    def call(self, message: str, timeout=120):
        if not self._connected.wait(timeout=timeout):
            raise Exception("RabbitMQ not connected")
        with self._lock:
            self.response = None
            self.corr_id = str(uuid.uuid4())
            self.channel.basic_publish(
                exchange='',
                routing_key='orchestrator',
                properties=pika.BasicProperties(
                    reply_to=self.callback_queue,
                    correlation_id=self.corr_id,
                    delivery_mode=pika.DeliveryMode.Persistent
                ),
                body=message
            )
            # Wait for response
            start = time.time()
            while self.response is None and (time.time() - start) < timeout:
                time.sleep(0.01)
            if self.response is None:
                raise TimeoutError("No response from RPC call")
            return self.response

    def close(self):
        self._closing = True
        if self.connection:
            self.connection.close()
        self._connected.clear()

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
