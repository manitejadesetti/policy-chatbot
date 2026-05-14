# Centralized env loading – handles load_dotenv once
import app.config  # noqa: F401

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import health
from app.api import chatbot
from app.api import documents


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)   

app.include_router(
    health.router,
    prefix="/api",
    tags=["v1"]
)

app.include_router(
    chatbot.router,
    prefix="/api/chat",
    tags=["v1"]
)

app.include_router(
    documents.router,
    prefix="/api/documents",
    tags=["v1"]
)   
    
