from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import pika
from pydantic import BaseModel
from dotenv import load_dotenv
import os

from contextlib import asynccontextmanager

from openai_manager import OpenAiManager
from agents.diagram_agent import DiagramAgent
from agents.text_agent import TextAgent
from agents.software_agent import SoftwareAgent
    
class RabbitMQPublisher:
    def __init__(self, host='localhost'):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=host))
        self.channel = self.connection.channel()
        # Ensure all queues exist (idempotent)
        self.channel.queue_declare(queue='diagram', durable=True)
        self.channel.queue_declare(queue='text', durable=True)
        self.channel.queue_declare(queue='software', durable=True)

    def publish(self, queue_name, message):
        self.channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=message.encode('utf-8'),
            properties=pika.BasicProperties(delivery_mode=2)  # make message persistent
        )

    def close(self):
        self.connection.close()


class Router:
    def __init__(self):
        self.publisher = RabbitMQPublisher(host='rabbitmq')  # Use 'rabbitmq' for Docker Compose

    def route(self, agent_name: str, request: str) -> str:
        if agent_name == "DiagramAgent":
            self.publisher.publish('diagram', request)
            return "Message sent to DiagramAgent queue"
        elif agent_name == "TextAgent":
            self.publisher.publish('text', request)
            return "Message sent to TextAgent queue"
        elif agent_name == "SoftwareAgent":
            self.publisher.publish('software', request)
            return "Message sent to SoftwareAgent queue"
        else:
            return "Error"

    def close(self):
        self.publisher.close()


class Orchestrator:
    def __init__(self, oai_manager, router):
        self.oai_manager = oai_manager
        self.router = router

    async def get_agent_name_w_ai(self, request: str) -> str:
        """
        This function uses OpenAI to determine which agent should handle the request. and returns one of three options:
        "DiagramAgent", "TextAgent", or "SoftwareAgent".

        If the request does not match any of these categories, it returns "UnknownAgent".
        """

        req = request.lower()
        response = await self.oai_manager.get_response(message=req)
        return response['response']

    async def route(self, request: str) -> str:
        agent_name = await self.get_agent_name_w_ai(request)
        return self.router.route(agent_name, request)

# Adjust the path if your .env is in the project root
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))

@asynccontextmanager
async def lifespan(app: FastAPI):
    oai_manager = OpenAiManager(api_key=os.getenv("OPENAI_API_KEY"))
    await oai_manager.get_available_models()
    router = Router()
    orchestrator = Orchestrator(oai_manager, router)
    app.state.oai_manager = oai_manager
    app.state.router = router
    app.state.orchestrator = orchestrator
    yield
    router.close()

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def strip_outer_quotes(s):
    s = s.strip()
    # Remove one layer of quotes if present
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s = s[1:-1]
    # Remove escaped quotes if present
    if (s.startswith('\\"') and s.endswith('\\"')) or (s.startswith("\\'") and s.endswith("\\'")):
        s = s[2:-2]
    return s

@app.get("/models")
async def get_models(request: Request):
    oai_manager = request.app.state.oai_manager
    return {"available_models": oai_manager.available_models}

class QuestionModel(BaseModel):
    text: str

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
    
    orchestrator = request.app.state.orchestrator
    response = await orchestrator_route(question.text, orchestrator)
    if response is None:
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
    response = strip_outer_quotes(response)
    return {"response": response}

# This function is used to handle the user question and generate a response
async def orchestrator_route(question: str, orchestrator):
    """
    This function is the orchestrator used to handle the user question and generate a response.
    Expects a question string and returns a JSON response with the generated content.
    Returns a JSON response with "user_response":"response" or an error message if the generation fails.
    """
    successful_generation = False
    error_message = None
    max_retries = int(os.getenv("MAX_RETRIES", 3))
    retry_count = 0
    response = None
    while not successful_generation and retry_count < max_retries:
        try:
            response = await orchestrator.route(question)
            if response and response != "Error":  # for valid responses
                successful_generation = True
            else: # for invalid responses
                print(f"Invalid response: {response}")
                retry_count += 1
                continue
        except Exception as e: # for exceptions
            error_message = str(e)
            print(f"An error occurred: {error_message}")
            print("Retrying to generate new product variations...")
            retry_count += 1
    if not successful_generation:
        print("Failed to generate successful product variations after retries.")
        return {"error": "Failed to process the request after multiple attempts."}
    
    return response
