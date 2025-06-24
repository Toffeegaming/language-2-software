from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse
from openai import AsyncOpenAI

from typing import List, Dict, Optional
import asyncio
import logging
import os
import json

class OpenAiManager:
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
        self.available_models = []

    async def get_available_models(self):
        try:
            all_models=[]
            async for model in self.client.models.list():
                all_models.append(model.id)
            # Filter for chat/completion models if needed
            print(f"Available models: {all_models}")
            self.available_models = all_models
        except Exception as e:
            print(f"Error fetching models: {e}")
            self.available_models = []

    async def get_response(self, message: str):
        response = await self.client.responses.create(
            model=self.available_models[7],
            instructions="""
            You are an orchestrator that routes requests to different agents based on the content of the request.

            You have three agents at your disposal:
                1. DiagramAgent: Handles requests related to diagrams and visualizations.
                2. TextAgent: Handles requests related to text generation and explanations. 
                3. SoftwareAgent: Handles requests related to software development and coding tasks.

            Please return either "DiagramAgent", "TextAgent", or "SoftwareAgent" based on the request content.
            If the request does not match any of these categories, return "UnknownAgent".

            return just the name of the agent without any additional text.
            """,
            input=message,
        )
        return {"message": "Test successful", "response": response.output_text}
    
from agents.diagram_agent import DiagramAgent
from agents.text_agent import TextAgent
from agents.software_agent import SoftwareAgent

class Orchestrator:
    def __init__(self):
        self.agents = {
            "diagram": DiagramAgent(),
            "text": TextAgent(),
            "software": SoftwareAgent()
        }

    async def route(self, request: str) -> str:
        req = request.lower()

        # Create an instance of OpenAiManager and fetch models if needed
        api_key = os.getenv("OPENAI_API_KEY")
        openai_manager = OpenAiManager(api_key)
        await openai_manager.get_available_models()
        response = await openai_manager.get_response(req)
        print(f"Response from OpenAI: {response['response']}")

        if response['response'] == "DiagramAgent":
            return self.agents["diagram"].handle(request)
        elif response['response'] == "TextAgent":
            return self.agents["text"].handle(request)
        elif response['response'] == "SoftwareAgent":
            return self.agents["software"].handle(request)
        else:
            return "❌ Sorry, I couldn't figure out what you want."

app = FastAPI()

@app.post('/api/handle-question')
async def handle_question(
    request: Request,
):
    """
    """

    data = await request.json()
    question = data.get("question", "").strip()

    response = await question_orchestrator(question)

    if response is None:
        raise HTTPException(status_code=500, detail="Internal Server Error")


    return JSONResponse(content=response)

# This function is used to handle the user question and generate a response
async def question_orchestrator(question: str):
    """This function is the orchestrator used to handle the user question and generate a response."""
    successful_generation = False
    error_message = None
    max_retries = int(os.getenv("MAX_RETRIES", 3))
    retry_count = 0
    response = None

    orchestrator = Orchestrator()

    while not successful_generation and retry_count < max_retries:
        try:
            response = await orchestrator.route(question)

            if response:
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