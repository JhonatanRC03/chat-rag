from typing import AsyncGenerator, List, Dict, Any
from openai import OpenAI
from app.core.config import settings
from app.utils.azure_search_helper import AzureAISearchHelper


class ChatService:
    """Service for handling chat with RAG functionality"""
    
    def __init__(self):
        # Initialize OpenAI client for chat (using Azure endpoint)
        self.chat_client = OpenAI(
            base_url=settings.AZURE_OPENAI_CHAT_ENDPOINT,
            api_key=settings.AZURE_OPENAI_CHAT_API_KEY
        )
        
        # Initialize search helper for RAG
        self.search_helper = AzureAISearchHelper()
        
    def get_system_prompt(self) -> str:
        """Get the system prompt for the chat assistant"""
        return """Eres un asistente inteligente especializado en responder preguntas basándote en documentos proporcionados.

INSTRUCCIONES:
1. Usa ÚNICAMENTE la información de los documentos proporcionados para responder
2. Si la información no está en los documentos, di claramente que no tienes esa información
3. Proporciona respuestas precisas, concisas y útiles
4. Cita las fuentes cuando sea relevante mencionando el nombre del documento
5. Si hay múltiples documentos relevantes, puedes combinar la información
6. Mantén un tono profesional pero amigable
7. Si la pregunta no está relacionada con los documentos, redirige amablemente al usuario

FORMATO DE RESPUESTA:
- Responde de manera directa y clara
- Usa bullet points cuando sea apropiado
- Menciona las fuentes al final si es relevante

Recuerda: Solo usa la información de los documentos proporcionados en el contexto."""

    async def search_relevant_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant documents using vector search"""
        try:
            print(f"Buscando documentos para: {query}")
            
            # Generate embeddings for the query
            query_embedding = await self.search_helper.generate_embeddings(query)
            if not query_embedding:
                print("No se pudieron generar embeddings para la consulta")
                return []
            
            print(f"Embeddings generados, dimensión: {len(query_embedding)}")
            
            # Search for relevant documents
            search_results = await self.search_helper.vector_search(
                query_vector=query_embedding,
                top_k=top_k
            )
            
            print(f"Documentos encontrados: {len(search_results)}")
            return search_results if search_results else []
            
        except Exception as e:
            print(f"Error searching documents: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def format_context_from_documents(self, documents: List[Dict[str, Any]]) -> str:
        """Format the retrieved documents into context for the chat"""
        if not documents:
            return "No se encontraron documentos relevantes."
        
        context_parts = []
        context_parts.append("DOCUMENTOS RELEVANTES:")
        context_parts.append("=" * 50)
        
        for i, doc in enumerate(documents, 1):
            # Extract document information
            content = doc.get('content', '')
            source_file = doc.get('sourcefile', 'Documento desconocido')
            source_page = doc.get('sourcepage', '')
            
            # Format document section
            context_parts.append(f"\n[DOCUMENTO {i}]")
            context_parts.append(f"Archivo: {source_file}")
            if source_page:
                context_parts.append(f"Página: {source_page}")
            context_parts.append("-" * 30)
            context_parts.append(content[:1000] + "..." if len(content) > 1000 else content)
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    async def chat_stream(
        self, 
        message: str, 
        conversation_history: List[Dict[str, str]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming chat response with RAG
        
        Args:
            message: User's message
            conversation_history: Previous conversation messages
            
        Yields:
            str: Streaming response chunks
        """
        try:
            print(f"Iniciando chat stream para mensaje: {message}")
            
            # Search for relevant documents
            relevant_docs = await self.search_relevant_documents(message, top_k=3)
            print(f"Documentos relevantes obtenidos: {len(relevant_docs)}")
            
            # Format context from documents
            context = self.format_context_from_documents(relevant_docs)
            
            # Prepare messages for the chat
            messages = [
                {"role": "system", "content": self.get_system_prompt()},
                {"role": "system", "content": f"CONTEXTO:\n{context}"}
            ]
            
            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history[-6:])  # Keep last 6 messages
            
            # Add current user message
            messages.append({"role": "user", "content": message})
            
            print(f"Enviando {len(messages)} mensajes al modelo")
            
            # Generate streaming response
            stream = self.chat_client.chat.completions.create(
                model=settings.AZURE_OPENAI_CHAT_DEPLOYMENT_NAME,
                messages=messages,
                stream=True,
                temperature=0.3,
                max_tokens=1000,
                top_p=0.9
            )
            
            # print("Stream iniciado, procesando chunks...")
            
            # Yield streaming chunks
            chunk_count = 0
            for chunk in stream:
                chunk_count += 1
                # print(f"Procesando chunk {chunk_count}")
                
                if not chunk.choices:
                    print(f"Chunk {chunk_count} sin choices")
                    continue
                    
                if len(chunk.choices) == 0:
                    print(f"Chunk {chunk_count} con choices vacío")
                    continue
                    
                delta = chunk.choices[0].delta
                if not delta:
                    print(f"Chunk {chunk_count} sin delta")
                    continue
                    
                if not hasattr(delta, 'content'):
                    print(f"Chunk {chunk_count} delta sin content")
                    continue
                    
                if delta.content is not None:
                    # print(f"Chunk {chunk_count} enviando contenido: {delta.content[:50]}...")
                    yield delta.content
                else:
                    print(f"Chunk {chunk_count} content es None")
            
            print(f"Stream completado. Total chunks procesados: {chunk_count}")
                    
        except Exception as e:
            error_message = f"Error en el chat: {str(e)}"
            print(error_message)
            yield f"Lo siento, ocurrió un error al procesar tu mensaje: {str(e)}"
    
    async def chat_simple(self, message: str) -> str:
        """
        Generate a simple non-streaming chat response with RAG
        
        Args:
            message: User's message
            
        Returns:
            str: Complete response
        """
        try:
            response_chunks = []
            async for chunk in self.chat_stream(message):
                response_chunks.append(chunk)
            return "".join(response_chunks)
            
        except Exception as e:
            return f"Error: {str(e)}"