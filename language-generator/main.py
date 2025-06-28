from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
import os
from openai_manager import OpenAiManager
import logfire
import pika
import threading
import asyncio

class RabbitManager:
    def __init__(self, oai_manager: OpenAiManager):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq'))
        self.thread = None
        self.oai_manager = oai_manager

    def get_channel(self):
        return self.connection.channel()

    def start_in_background(self):
        self.thread = threading.Thread(target=self.setup_queue, daemon=True)
        self.thread.start()

    async def process_message(self, message):
        print("Got request...")
        response = await self.oai_manager.get_response(message)
        print("Returning request...")
        return response

    def setup_queue(self):
        channel = self.get_channel()
        channel.queue_declare(queue='language-generator', durable=True)

        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(queue='language-generator', on_message_callback=self.on_request)

        print("Waiting RPC request on 'language-generator' queue.")
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
    oai_manager = OpenAiManager(api_key=os.getenv("OPENAI_API_KEY"))
    await oai_manager.get_available_models()

    app.state.oai_manager = oai_manager

    app.state.rabbit_manager = RabbitManager(oai_manager)
    app.state.rabbit_manager.start_in_background()
    yield
    app.state.rabbit_manager.close()

app = FastAPI(lifespan=lifespan)

logfire.configure(token=os.getenv("LOGFIRE_WRITE_TOKEN"), service_name="language-generator")
logfire.instrument_fastapi(app, capture_headers=True)

@app.head("/")
async def health_check():
    return {"status": "ok"}

@app.get("/models")
async def get_models(request: Request):
    oai_manager = request.app.state.oai_manager
    return {"available_models": oai_manager.available_models}
