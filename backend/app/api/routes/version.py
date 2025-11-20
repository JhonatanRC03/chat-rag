from fastapi import APIRouter
from app.core.config import settings

router = APIRouter()

@router.get("/")
async def get_version():
    """Get API version"""
    return {
        "version": settings.VERSION or "1.0.0",
        "status": "running",
        "title": "Agente IA Admin Backend"
    }