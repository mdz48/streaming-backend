from fastapi import FastAPI
from app.shared.config.database import init_db
from app.features.user.routes.user_routes import router as user_router
from fastapi.middleware.cors import CORSMiddleware
from app.shared.config.database import init_db
from websocket import router as ws_router, manager

app = FastAPI(title="Streaming API")

app.include_router(user_router, prefix="/api", tags=["Users"])
app.include_router(ws_router, tags=["WebSocket"])

@app.get("/api/streams/active", tags=["Streams"])
async def get_active_streams():
    """Obtener lista de streams activos actualmente"""
    return {"streams": manager.get_active_streams()}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

init_db()
