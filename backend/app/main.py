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
origins = [str(origin).rstrip("/") for origin in settings.BACKEND_CORS_ORIGINS] if settings.BACKEND_CORS_ORIGINS else []
# Ensure all origins have protocol prefix (e.g. prepending https:// if host-only)
origins = [f"https://{org}" if not org.startswith("http") else org for org in origins]

# Add explicit required origins to be absolutely sure
required_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "https://ai-based-smart-doubt-management-system-1.onrender.com"
]
for req_org in required_origins:
    if req_org not in origins:
        origins.append(req_org)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.onrender\.com|http://localhost(:\d+)?|http://127\.0\.0\.1(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API V1 Routing Group
@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):
    import traceback
    from fastapi.responses import JSONResponse
    tb = traceback.format_exc()
    logger.error(f"Unhandled server exception: {tb}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "traceback": tb}
    )

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
    token: str = Query(None)
):
    """Real-time bidirectional WebSocket coordinate channel."""
    roles = ["student", "tutor", "admin"]
    if token:
        payload = security.verify_token(token)
        if payload and payload.get("roles"):
            roles = payload.get("roles")
            
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
