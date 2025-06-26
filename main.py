from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.memory import InMemoryMemoryService
from google.genai import types
from dotenv import load_dotenv
from uuid import uuid4
from chatbot_agent.job_agent import job_agent
from chatbot_agent.ecommerce_agent import ecommerce_agent
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional



load_dotenv()

app = FastAPI()

origins = []

app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"]
)

API_KEYS = {
    "api_key_123" : "job_agent",
    "api_key_456" : "ecommerce_agent"
}

session_service = InMemorySessionService()
memory_service = InMemoryMemoryService()

#Input Format
class MessageInput(BaseModel):
    message : str 
    user_id : str = "guest123"
    session_id: str = str(uuid4())

@app.get("/")
def root():
    return {
        "message" : "Multi agents API running"
    }

@app.post("/chat")
async def chat(data: MessageInput, x_api_key : Optional[str] = Header(None)):    
    if x_api_key not in API_KEYS:
        raise HTTPException(status_code=401, detail="Not available APIs")
    
    if x_api_key == "api_key_123":
        app_name = "Job Seeking Helper"
        agent = job_agent
    elif x_api_key == "api_key_456":
        app_name = "Ecommerce Website Assistant"
        agent = ecommerce_agent


    existing_session = await session_service.get_session(
        session_id=data.session_id,
        app_name=app_name,
        user_id=data.user_id
        )

    if not existing_session:
        session_service.create_session(
            app_name=app_name,
            user_id=data.user_id,
            session_id=data.session_id
        )

    runner = Runner(
        app_name=app_name,
        agent=agent,
        session_service=session_service,
        memory_service=memory_service
    )

    user_message = types.Content(
        role="user", parts=[types.Part(text=data.message)]
    )

    result_text = ""
    async for event in runner.run_async(
        user_id=data.user_id,
        session_id=data.session_id,
        new_message=user_message
    ):
        if event.is_final_response() and event.content.parts:
            result_text = event.content.parts[0].text

    return {"response": result_text, "session" : data.session_id} 
