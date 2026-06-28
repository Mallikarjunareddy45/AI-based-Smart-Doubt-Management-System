from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, status
from fastapi.middleware.cors import CORSMiddleware
import json
import logging

from app.core.config import settings
from app.core.ws_manager import manager
from app.core import security
from app.api.v1 import api_router

# Setup logger configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn.error")

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Smart AI-powered Doubt Routing & Semantic Clustering Engine APIs",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# CORS configurations
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).rstrip("/") for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Mount API V1 Routing Group
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def read_root():
    return {
        "status": "online", 
        "project": settings.PROJECT_NAME,
        "docs_url": "/docs"
    }


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    user_id: str, 
    token: str = Query(...)
):
    """Real-time bidirectional WebSocket coordinate channel."""
    # 1. Handshake token check
    payload = security.verify_token(token)
    if not payload or payload.get("sub") != user_id:
        logger.warning(f"WebSocket auth failed for user: {user_id}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
        
    roles = payload.get("roles", [])
    await manager.connect(websocket, user_id, roles)
    
    # 2. Connection event loop
    try:
        while True:
            # Await client actions
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                action = message.get("action")
                
                if action == "join_room":
                    cluster_id = message.get("cluster_id")
                    if cluster_id:
                        manager.join_cluster_room(user_id, cluster_id)
                        await websocket.send_text(json.dumps({
                            "event": "room_joined", 
                            "cluster_id": str(cluster_id)
                        }))
                        
                elif action == "leave_room":
                    cluster_id = message.get("cluster_id")
                    if cluster_id:
                        manager.leave_cluster_room(user_id, cluster_id)
                        await websocket.send_text(json.dumps({
                            "event": "room_left", 
                            "cluster_id": str(cluster_id)
                        }))
                        
            except json.JSONDecodeError:
                logger.error("WebSocket received non-JSON payload")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        
    except Exception as e:
        logger.error(f"WebSocket loop exception: {e}")
        manager.disconnect(websocket, user_id)
