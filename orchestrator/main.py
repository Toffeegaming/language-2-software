from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import logfire
from pydantic_ai import Agent
from contextlib import asynccontextmanager
import pika
import threading
import uuid
import time
import asyncio

class RabbitSender:
    def __init__(self):
        self.connection = None
        self.channel = None
        self.callback_queue = None
        self.responses = {}
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
        corr_id = properties.correlation_id
        with self._lock:
            if corr_id in self.responses:
                self.responses[corr_id] = body

    def call(self, message: str, routing_key: str, timeout=10):
        if not self._connected.wait(timeout=timeout):
            raise Exception("RabbitMQ not connected")
        corr_id = str(uuid.uuid4())
        with self._lock:
            self.responses[corr_id] = None
            self.channel.basic_publish(
                exchange='',
                routing_key=routing_key,
                properties=pika.BasicProperties(
                    reply_to=self.callback_queue,
                    correlation_id=corr_id,
                    delivery_mode=pika.DeliveryMode.Persistent
                ),
                body=message
            )
        # Wait for response
        start = time.time()
        while True:
            with self._lock:
                response = self.responses[corr_id]
            if response is not None:
                with self._lock:
                    del self.responses[corr_id]
                return response
            if (time.time() - start) > timeout:
                with self._lock:
                    del self.responses[corr_id]
                raise TimeoutError("No response from RPC call")
            time.sleep(0.01)

    def close(self):
        self._closing = True
        if self.connection:
            self.connection.close()
        self._connected.clear()

rabbit_sender = RabbitSender()

def call_language_agent(request: str) -> str:
    """
    Calls the language agent to generate text based on the request.
    """
    try:
        return rabbit_sender.call(request, routing_key="language-agent")
    except Exception as e:
        return f"Error calling language-agent: {e}"

def call_diagram_agent(request: str) -> str:
    """
    Calls the diagram agent to generate diagrams based on the request.
    """
    try:
        return rabbit_sender.call(request, routing_key="diagram-agent")
    except Exception as e:
        return f"Error calling diagram-agent: {e}"

def call_software_agent(request: str) -> str:
    """
    Calls the software agent to generate software based on the request.
    """
    try:
        return rabbit_sender.call(request, routing_key="software-agent")
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
    agent = Agent(
        'gpt-4o-2024-05-13',
        deps_type=str,
        tools=[call_language_agent, call_diagram_agent, call_software_agent],
        system_prompt=(
            "You're an orchestrating agent. You use your tools to call other agents to generate text, diagrams, or software based on user requests. You do not generate text, diagrams, or software directly, but instead use your tools to call the agent services."
        ),
        instrument=True,
    )

    app.state.rabbit_manager = RabbitManager(agent)
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

@app.head("/")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "ok"}
