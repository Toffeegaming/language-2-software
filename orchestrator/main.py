from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import os
from contextlib import asynccontextmanager

from .openai_manager import OpenAiManager
from .agents.diagram_agent import DiagramAgent
from .agents.text_agent import TextAgent
from .agents.software_agent import SoftwareAgent
    
class Orchestrator:
    def __init__(self):
        self.agents = {
            "diagram": DiagramAgent(),
            "text": TextAgent(),
            "software": SoftwareAgent()
        }

    async def get_agent_name_w_ai(self, request: str) -> str:
        """
        This function uses OpenAI to determine which agent should handle the request. and returns one of three options:
        "DiagramAgent", "TextAgent", or "SoftwareAgent".

        If the request does not match any of these categories, it returns "UnknownAgent".
        """
        req = request.lower()
        api_key = os.getenv("OPENAI_API_KEY")
        openai_manager = OpenAiManager(api_key)
        await openai_manager.get_available_models()
        instructions = """
        You are an orchestrator that routes requests to different agents based on the content of the request.

        You have three agents at your disposal:
            1. DiagramAgent: Handles requests related to diagrams and visualizations.
            2. TextAgent: Handles requests related to text generation and explanations. 
            3. SoftwareAgent: Handles requests related to software development and coding tasks.

        Please return either "DiagramAgent", "TextAgent", or "SoftwareAgent" based on the request content.
        If the request does not match any of these categories, return "UnknownAgent".

        return just the name of the agent without any additional text.
        """
        response = await openai_manager.get_response(req, instructions)
        print(f"Response from OpenAI: {response['response']}")
        return response['response']

    async def route(self, request: str) -> str:
        agent_name = await self.get_agent_name_w_ai(request)
        if agent_name == "DiagramAgent":
            return self.agents["diagram"].handle(request)
        elif agent_name == "TextAgent":
            return self.agents["text"].handle(request)
        elif agent_name == "SoftwareAgent":
            return self.agents["software"].handle(request)
        else:
            return "Error"

@asynccontextmanager
async def lifespan(app: FastAPI):
    oai_manager = OpenAiManager(api_key=os.getenv("OPENAI_API_KEY"))
    await oai_manager.get_available_models()

    app.state.oai_manager = oai_manager

    yield
    
app = FastAPI(lifespan=lifespan)

@app.post('/api/handle-question')
async def handle_question(
    request: Request,
):
    """
    Expects a JSON body with a "question" field.
    Example:
    {
        "question": "Please create code for this... /Please create a diagram for this... /Please create a text for this..."
    }
    """

    data = await request.json()
    question = data.get("question", "").strip()

    response = await question_orchestrator(question)

    if response is None:
        raise HTTPException(status_code=500, detail="Internal Server Error")


    return JSONResponse(content=response)

# This function is used to handle the user question and generate a response
async def question_orchestrator(question: str):
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

    orchestrator = Orchestrator()

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

    return {"user_response": response}