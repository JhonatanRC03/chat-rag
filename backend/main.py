from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.core.config import settings
from app.core.database import init_database


app = FastAPI(
    title="Agente IA Admin Backend",
    version=settings.VERSION,
)


if isinstance(settings.BACKEND_CORS_ORIGINS, str):
    allow_origins = [
        origin.strip() for origin in settings.BACKEND_CORS_ORIGINS.split(",")
    ]
else:
    allow_origins = settings.BACKEND_CORS_ORIGINS


if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.on_event("startup")
async def start_database():
    await init_database()


app.include_router(api_router, prefix="/api/v1")