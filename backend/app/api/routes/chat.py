from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
from app.services.chat_service import ChatService
import json

router = APIRouter()

class ChatMessage(BaseModel):
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = None

class ChatResponse(BaseModel):
    response: str
    success: bool = True

# Dependency injection
def get_chat_service():
    return ChatService()

@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Stream chat response with RAG functionality
    
    Args:
        request: Chat request with message and optional conversation history
        
    Returns:
        StreamingResponse: Server-sent events stream
    """
    try:
        async def generate_response():
            """Generate streaming response in SSE format"""
            try:
                async for chunk in chat_service.chat_stream(
                    message=request.message,
                    conversation_history=request.conversation_history
                ):
                    # Format as Server-Sent Events
                    yield f"data: {json.dumps({'chunk': chunk, 'done': False})}\n\n"
                
                # Send completion signal
                yield f"data: {json.dumps({'chunk': '', 'done': True})}\n\n"
                
            except Exception as e:
                error_data = json.dumps({
                    'error': str(e), 
                    'done': True,
                    'chunk': f"Error: {str(e)}"
                })
                yield f"data: {error_data}\n\n"
        
        return StreamingResponse(
            generate_response(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/message", response_model=ChatResponse)
async def chat_message(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Send a chat message and get complete response (non-streaming)
    
    Args:
        request: Chat request with message and optional conversation history
        
    Returns:
        ChatResponse: Complete chat response
    """
    try:
        response = await chat_service.chat_simple(request.message)
        
        return ChatResponse(
            response=response,
            success=True
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def chat_health():
    """Health check endpoint for chat service"""
    return {"status": "healthy", "service": "chat"}