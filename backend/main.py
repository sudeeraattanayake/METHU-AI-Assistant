from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.chat import router as chat_router
from backend.api.websocket import router as websocket_router


app = FastAPI(
    title="METHU API",
    description="Multimodal Executive & Task Handling Unit",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # development only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(chat_router)
app.include_router(websocket_router)


@app.get("/")
async def root():
    return {
        "name": "METHU",
        "status": "online",
        "version": "0.1.0",
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "system": "METHU",
    }
