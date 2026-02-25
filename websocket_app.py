from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from websocket import router as ws_router, manager

app = FastAPI(title="WebSocket Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

app.include_router(ws_router, tags=["Streams"])


@app.get("/streams/active", tags=["Streams"])
async def get_active_streams():
    """Obtener lista de streams activos actualmente"""
    return {"streams": manager.get_active_streams()}