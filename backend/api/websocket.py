from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.graphs.methu_graph import methu_graph


router = APIRouter()


@router.websocket("/ws/methu")
async def methu_websocket(websocket: WebSocket):

    await websocket.accept()

    await websocket.send_json(
        {
            "event": "methu_connected",
            "payload": {
                "status": "online",
                "message": "METHU connection established",
            },
        }
    )

    try:
        while True:

            data = await websocket.receive_json()

            message = data.get("message", "").strip()
            session_id = data.get("session_id", "default")

            if not message:
                await websocket.send_json(
                    {
                        "event": "methu_error",
                        "payload": {
                            "message": "No message provided."
                        },
                    }
                )
                continue

            # Tell holographic UI METHU is thinking.
            await websocket.send_json(
                {
                    "event": "methu_thinking",
                    "payload": {
                        "message": message,
                    },
                }
            )

            result = methu_graph.invoke(
                {
                    "user_input": message,
                    "session_id": session_id,
                    "status": "idle",
                }
            )

            await websocket.send_json(
                {
                    "event": result.get(
                        "ui_event",
                        "methu_speaking",
                    ),
                    "payload": result.get(
                        "ui_payload",
                        {},
                    ),
                    "response": result.get(
                        "final_response"
                    ),
                    "agent": result.get(
                        "selected_agent"
                    ),
                    "status": result.get(
                        "status"
                    ),
                }
            )

    except WebSocketDisconnect:
        pass
