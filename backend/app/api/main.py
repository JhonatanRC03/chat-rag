import logging
import sys
from fastapi import APIRouter
from app.api.routes import (
    version,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.StreamHandler(sys.stderr)],
)

logger = logging.getLogger(__name__)
logging.getLogger("azure").setLevel(logging.WARNING)
# logging.getLogger("urllib3").setLevel(logging.WARNING)

api_router = APIRouter()

api_router.include_router(version.router, prefix="/version", tags=["version"])