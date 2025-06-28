from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import os
import logfire
from pydantic_ai import Agent
import requests
import pika
import threading
import asyncio

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
        channel.queue_declare(queue='software-agent', durable=True)

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue='software-agent', on_message_callback=self.on_request)

        print("Waiting RPC request on 'software-agent' queue.")
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
        tools=[call_code_generator],
        system_prompt=(
            "You're a software agent. You generate code based on user requests. Use your different tools to create code in the requested format and language."
        ),
        instrument=True,
    )

    app.state.rabbit_manager = RabbitManager(agent)
    app.state.rabbit_manager.start_in_background()
    yield
    app.state.rabbit_manager.close()

app = FastAPI(lifespan=lifespan)
logfire.instrument_fastapi(app, capture_headers=True)

@app.head("/")
async def health_check():
    return {"status": "ok"}
