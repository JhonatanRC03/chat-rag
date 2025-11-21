from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class DocumentUploadResponse(BaseModel):
    """Response simple para upload de documentos"""
    success: bool
    message: str
    document_id: Optional[str] = None
    processing_summary: Optional[Dict[str, str]] = None
    document_info: Optional[Dict[str, Any]] = None
    analysis_summary: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: Optional[datetime] = None


class ErrorResponse(BaseModel):
    """Response de error estandarizada"""
    success: bool = False
    message: str
    error: str
    timestamp: datetime = datetime.now()