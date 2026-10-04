from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from backend.graphs.methu_graph import methu_graph


router = APIRouter(
    prefix="/api",
    tags=["METHU"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"


@router.post("/chat")
async def chat(request: ChatRequest):
    try:
        result = methu_graph.invoke(
            {
                "user_input": request.message,
                "session_id": request.session_id,
                "status": "idle",
            }
        )

        return {
            "success": True,
            "session_id": request.session_id,
            "agent": result.get("selected_agent"),
            "intent": result.get("intent"),
            "language": result.get("language"),
            "status": result.get("status"),
            "response": result.get("final_response"),
            "ui_event": result.get("ui_event"),
            "ui_payload": result.get("ui_payload", {}),
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )
