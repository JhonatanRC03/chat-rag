from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from typing import Optional
import os

from app.services.document_processor import DocumentProcessorService

router = APIRouter()

# Dependency injection
def get_document_processor() -> DocumentProcessorService:
    return DocumentProcessorService()


@router.post("/upload-and-process")
async def upload_and_process_document(
    file: UploadFile = File(..., description="PDF file to upload and process"),
    file_path: Optional[str] = Form(None, description="Optional: local file path instead of upload"),
    processor: DocumentProcessorService = Depends(get_document_processor)
):
    """    
    Procesa documento completo: Blob Storage + Document Intelligence + Embeddings + AI Search
    """
    try:
        # Validar y obtener contenido del archivo
        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                file_content = f.read()
            filename = os.path.basename(file_path)
            content_type = "application/pdf"
        else:
            if not file.filename or not file.filename.lower().endswith('.pdf'):
                raise HTTPException(status_code=400, detail="Only PDF files are supported")
            
            file_content = await file.read()
            filename = file.filename
            content_type = file.content_type or "application/pdf"
        
        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="File is empty")
        
        # Procesar documento completo
        result = await processor.process_complete_document(
            file_content=file_content,
            filename=filename,
            content_type=content_type
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

