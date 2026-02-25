from fastapi import FastAPI
from app.shared.config.database import init_db
from app.features.user.routes.user_routes import router as user_router
from fastapi.middleware.cors import CORSMiddleware
from app.shared.config.database import init_db

app = FastAPI(title="Streaming API")

app.include_router(user_router, prefix="/api", tags=["Users"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

init_db()
