from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Existing METHU API routers
from backend.api.chat import router as chat_router
from backend.api.websocket import router as websocket_router

# Gemini Sinhala Female Voice API
from backend.voice_api import router as voice_router


# FastAPI application
app = FastAPI(
    title="METHU API",
    description="Multimodal Executive & Task Handling Unit",
    version="0.1.0",
)


# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register API routers
app.include_router(chat_router)
app.include_router(websocket_router)
app.include_router(voice_router)


# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "METHU",
        "status": "online",
        "version": "0.1.0",
    }


# Health endpoint
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "system": "METHU",
    }
