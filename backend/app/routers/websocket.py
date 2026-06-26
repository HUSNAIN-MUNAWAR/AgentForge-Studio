from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.app.services.event_bus import event_bus

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/runs/{run_id}")
async def run_socket(websocket: WebSocket, run_id: str):
    await websocket.accept()
    await websocket.send_json({"event_type": "connected", "run_id": run_id})
    try:
        async for event in event_bus.subscribe(run_id):
            await websocket.send_json(event)
    except WebSocketDisconnect:
        return
