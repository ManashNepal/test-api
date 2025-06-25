from fastapi import FastAPI
from pydantic import BaseModel
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from dotenv import load_dotenv
from uuid import uuid4
from chatbot_agent.agent import root_agent
from fastapi.middleware.cors import CORSMiddleware

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

session_service = InMemorySessionService()

#Input Format
class MessageInput(BaseModel):
    message : str 
    user_id : str = "guest123"
    session_id: str = ""

@app.get("/")
def root():
    return {
        "message" : "Job Assistant API is running"
    }

@app.post("/chat")
async def chat(data : MessageInput):
    if not data.session_id:
        data.session_id = str(uuid4())
    
    # Synchronous session handling
    session = session_service.get_session(
        session_id=data.session_id,
        app_name="Job Seeking Helper",
        user_id=data.user_id
    )

    if not session:
        session_service.create_session(
            app_name="Job Seeking Helper",
            user_id=data.user_id,
            session_id=data.session_id
        )

    runner = Runner(
        app_name="Job Seeking Helper",
        agent=root_agent,
        session_service=session_service
    )

    user_message = types.Content(
        role="user", parts=[types.Part(text=data.message)]
    )

    result_text = ""
    # Proper async handling for runner
    async for event in runner.run_async(
        user_id=data.user_id,
        session_id=data.session_id,
        new_message=user_message
    ):
        if event.is_final_response() and event.content.parts:
            result_text = event.content.parts[0].text

    return {"response": result_text, "session_id": data.session_id}
