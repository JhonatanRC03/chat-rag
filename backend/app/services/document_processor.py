"""
Servicio simplificado para procesamiento completo de documentos
Solo lo necesario: upload-and-process
"""
import uuid
import re
from datetime import datetime
from typing import Dict, Any, List

from app.utils.azure_blob_helper import AzureBlobStorageHelper
from app.utils.azure_search_helper import AzureAISearchHelper
from app.utils.document_intelligence_helper import AzureDocumentIntelligenceHelper


class DocumentProcessorService:
    """Servicio que maneja solo el procesamiento completo de documentos"""
    
    def __init__(self):
        self.blob_helper = AzureBlobStorageHelper()
        self.search_helper = AzureAISearchHelper()
        self.di_helper = AzureDocumentIntelligenceHelper()
    
    async def process_complete_document(
        self, 
        file_content: bytes, 
        filename: str, 
        content_type: str = "application/pdf"
    ) -> Dict[str, Any]:
        """
        Procesa completamente un documento: Blob + DI + Embeddings + Search
        
        Args:
            file_content: Contenido del archivo en bytes
            filename: Nombre del archivo
            content_type: Tipo de contenido
            
        Returns:
            dict: Resultado completo del procesamiento
        """
        document_id = str(uuid.uuid4())
        
        try:
            # 1. Subir a Blob Storage
            blob_result = await self.blob_helper.upload_file(
                file_content=file_content,
                filename=filename,
                content_type=content_type
            )
            
            if not blob_result["success"]:
                return self._error_response(f"Blob upload failed: {blob_result['error']}")
            
            # 2. Analizar con Document Intelligence
            analysis_result = await self.di_helper.extract_structured_data(file_content)
            
            if not analysis_result["success"]:
                # Cleanup blob si falla el análisis
                await self.blob_helper.delete_file(blob_result["blob_name"])
                return self._error_response(f"Document analysis failed: {analysis_result.get('error')}")
            
            # 3. Preparar para indexación
            search_document = self._prepare_search_document(
                document_id=document_id,
                filename=filename,
                blob_result=blob_result,
                analysis_result=analysis_result,
                content_type=content_type
            )
            
            # 4. Crear índice si no existe
            await self.search_helper.create_document_index()
            
            # 5. Indexar con embeddings
            index_result = await self.search_helper.index_document(search_document)
            
            if not index_result["success"]:
                # Cleanup si falla la indexación
                await self.blob_helper.delete_file(blob_result["blob_name"])
                return self._error_response(f"Search indexing failed: {index_result.get('error')}")
            
            # 6. Retornar resultado exitoso
            return self._success_response(
                document_id=document_id,
                filename=filename,
                blob_result=blob_result,
                analysis_result=analysis_result
            )
            
        except Exception as e:
            return self._error_response(f"Unexpected error: {str(e)}")
    
    def _prepare_search_document(
        self, 
        document_id: str, 
        filename: str, 
        blob_result: Dict, 
        analysis_result: Dict, 
        content_type: str
    ) -> Dict[str, Any]:
        """Preparar documento para indexación - solo campos necesarios"""
        extracted_text = analysis_result.get("text_content", "")
        
        return {
            "id": document_id,
            "content": extracted_text,
            "category": "document",  # Categoría por defecto
            "sourcepage": "1",  # Página por defecto
            "sourcefile": filename,
            "storageUrl": blob_result["blob_url"],
            "company": "default"  # Empresa por defecto
        }
    
    def _success_response(
        self, 
        document_id: str, 
        filename: str, 
        blob_result: Dict, 
        analysis_result: Dict
    ) -> Dict[str, Any]:
        """Generar respuesta de éxito estandarizada"""
        extracted_text = analysis_result.get("text_content", "")
        
        return {
            "success": True,
            "message": "Document processed successfully!",
            "document_id": document_id,
            "processing_summary": {
                "blob_storage": "uploaded",
                "document_intelligence": "analyzed", 
                "embeddings": "generated",
                "search_index": "indexed"
            },
            "document_info": {
                "id": document_id,
                "filename": filename,
                "blob_name": blob_result["blob_name"],
                "blob_url": blob_result["blob_url"],
                "file_size": blob_result["size"]
            },
            "analysis_summary": {
                "total_pages": analysis_result.get("total_pages", 0),
                "tables_count": analysis_result.get("tables_count", 0),
                "has_tables": analysis_result.get("metadata", {}).get("has_tables", False),
                "estimated_words": len(extracted_text.split()) if extracted_text else 0,
                "text_preview": extracted_text[:300] + "..." if len(extracted_text) > 300 else extracted_text
            }
        }
    
    def _error_response(self, error_msg: str) -> Dict[str, Any]:
        """Generar respuesta de error estandarizada"""
        return {
            "success": False,
            "message": "❌ Document processing failed",
            "error": error_msg,
            "timestamp": datetime.now().isoformat()
        }