from __future__ import annotations

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect

from .backend_client import BackendRelay
from .config import Settings
from .connection_manager import ConnectionManager
from .models import HeartbeatPayload, ObservationPayload

settings = Settings()
app = FastAPI(title="robot-bridge", version="1.0.0")
connections = ConnectionManager()
relay = BackendRelay(settings)


@app.get("/health")
async def health() -> dict:
    return {
        "status": "ok",
        "backend_base_url": settings.backend_base_url,
        "queued_events": len(relay.retry_queue),
    }


@app.post("/api/v1/heartbeat")
async def heartbeat(payload: HeartbeatPayload) -> dict:
    try:
        await relay.relay_heartbeat(payload)
    except Exception:
        await connections.broadcast("bridge.warning", {"message": "Backend relay failed for heartbeat"})

    await connections.broadcast("robot.heartbeat", payload.model_dump(mode="json"))
    return {"accepted": True}


@app.post("/api/v1/observation")
async def observation(payload: ObservationPayload) -> dict:
    try:
        await relay.relay_observation(payload)
    except Exception:
        await connections.broadcast("bridge.warning", {"message": "Backend relay failed for observation"})

    await connections.broadcast("robot.observation", payload.model_dump(mode="json"))
    return {"accepted": True}


@app.get("/api/v1/retry-queue")
async def retry_queue() -> dict:
    return {
        "size": len(relay.retry_queue),
        "events": [event.model_dump(mode="json") for event in relay.retry_queue],
    }


@app.websocket("/ws/robot")
async def robot_socket(websocket: WebSocket) -> None:
    await connections.connect(websocket)
    try:
        while True:
            message = await websocket.receive_json()
            await connections.broadcast("robot.command", message)
    except WebSocketDisconnect:
        connections.disconnect(websocket)
    except Exception as exc:
        connections.disconnect(websocket)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
