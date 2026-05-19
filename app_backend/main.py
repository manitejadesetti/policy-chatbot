# Centralized env loading – handles load_dotenv once

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app_backend.api import health
from app_backend.api import chatbot
from app_backend.api import documents


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
    
