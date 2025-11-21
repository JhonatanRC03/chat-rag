import io
from typing import Dict, Any, List, Optional
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from app.core.config import settings


class AzureDocumentIntelligenceHelper:
    """Helper class for Azure Document Intelligence operations"""
    
    def __init__(self):
        self.endpoint = settings.AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT
        self.key = settings.AZURE_DOCUMENT_INTELLIGENCE_KEY
        
        # Initialize the Document Analysis client
        self.client = DocumentAnalysisClient(
            endpoint=self.endpoint,
            credential=AzureKeyCredential(self.key)
        )
    
    async def analyze_document(
        self, 
        document_content: bytes, 
        model_id: str = "prebuilt-document"
    ) -> Dict[str, Any]:
        """
        Analyze a document using Azure Document Intelligence
        
        Args:
            document_content: The document content in bytes
            model_id: The model to use for analysis (default: prebuilt-document)
            
        Returns:
            dict: Analysis results including text, tables, key-value pairs, etc.
        """
        try:
            # Create a file-like object from bytes
            document_stream = io.BytesIO(document_content)
            
            # Analyze the document
            poller = self.client.begin_analyze_document(
                model_id=model_id,
                document=document_stream
            )
            
            result = poller.result()
            
            # Extract comprehensive information
            analysis_result = {
                "success": True,
                "content": result.content,
                "pages": [],
                "tables": [],
                "key_value_pairs": [],
                "entities": [],
                "styles": [],
                "languages": []
            }
            
            # Extract page information
            for page in result.pages:
                page_info = {
                    "page_number": page.page_number,
                    "width": page.width,
                    "height": page.height,
                    "unit": page.unit,
                    "angle": page.angle,
                    "lines": []
                }
                
                # Extract lines from each page
                for line in page.lines:
                    line_info = {
                        "content": line.content,
                        "bounding_polygon": [(point.x, point.y) for point in line.polygon] if line.polygon else [],
                        "spans": [{"offset": span.offset, "length": span.length} for span in line.spans] if line.spans else []
                    }
                    page_info["lines"].append(line_info)
                
                analysis_result["pages"].append(page_info)
            
            # Extract tables
            for table in result.tables:
                table_info = {
                    "row_count": table.row_count,
                    "column_count": table.column_count,
                    "cells": []
                }
                
                for cell in table.cells:
                    cell_info = {
                        "content": cell.content,
                        "row_index": cell.row_index,
                        "column_index": cell.column_index,
                        "row_span": cell.row_span,
                        "column_span": cell.column_span,
                        "kind": cell.kind,
                        "bounding_polygon": [(point.x, point.y) for point in cell.bounding_polygon] if cell.bounding_polygon else []
                    }
                    table_info["cells"].append(cell_info)
                
                analysis_result["tables"].append(table_info)
            
            # Extract key-value pairs
            for kv_pair in result.key_value_pairs:
                if kv_pair.key and kv_pair.value:
                    kv_info = {
                        "key": kv_pair.key.content if kv_pair.key else "",
                        "value": kv_pair.value.content if kv_pair.value else "",
                        "confidence": kv_pair.confidence
                    }
                    analysis_result["key_value_pairs"].append(kv_info)
            
            # Extract entities (if available)
            if hasattr(result, 'entities') and result.entities:
                for entity in result.entities:
                    entity_info = {
                        "content": entity.content,
                        "category": entity.category,
                        "sub_category": entity.sub_category,
                        "confidence": entity.confidence
                    }
                    analysis_result["entities"].append(entity_info)
            
            # Extract styles (if available)
            if hasattr(result, 'styles') and result.styles:
                for style in result.styles:
                    style_info = {
                        "is_handwritten": style.is_handwritten,
                        "confidence": style.confidence,
                        "spans": [{"offset": span.offset, "length": span.length} for span in style.spans] if style.spans else []
                    }
                    analysis_result["styles"].append(style_info)
            
            # Extract languages (if available)
            if hasattr(result, 'languages') and result.languages:
                for language in result.languages:
                    lang_info = {
                        "locale": language.locale,
                        "confidence": language.confidence,
                        "spans": [{"offset": span.offset, "length": span.length} for span in language.spans] if language.spans else []
                    }
                    analysis_result["languages"].append(lang_info)
            
            return analysis_result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "content": "",
                "pages": [],
                "tables": [],
                "key_value_pairs": [],
                "entities": [],
                "styles": [],
                "languages": []
            }
    
    async def analyze_layout(self, document_content: bytes) -> Dict[str, Any]:
        """
        Analyze document layout using the prebuilt-layout model
        
        Args:
            document_content: The document content in bytes
            
        Returns:
            dict: Layout analysis results
        """
        return await self.analyze_document(document_content, "prebuilt-layout")
    
    async def analyze_read(self, document_content: bytes) -> Dict[str, Any]:
        """
        Extract text using the prebuilt-read model (OCR)
        
        Args:
            document_content: The document content in bytes
            
        Returns:
            dict: Text extraction results
        """
        return await self.analyze_document(document_content, "prebuilt-read")
    
    async def extract_text_only(self, document_content: bytes) -> str:
        """
        Extract only the text content from a document
        
        Args:
            document_content: The document content in bytes
            
        Returns:
            str: Extracted text content
        """
        try:
            result = await self.analyze_document(document_content)
            if result["success"]:
                return result["content"]
            else:
                return ""
        except Exception as e:
            print(f"Error extracting text: {e}")
            return ""
    
    async def extract_structured_data(self, document_content: bytes) -> Dict[str, Any]:
        """
        Extract structured data including text, tables, and key-value pairs
        
        Args:
            document_content: The document content in bytes
            
        Returns:
            dict: Structured data extraction results
        """
        try:
            result = await self.analyze_document(document_content)
            
            if not result["success"]:
                return result
            
            # Create a structured summary
            structured_data = {
                "success": True,
                "text_content": result["content"],
                "total_pages": len(result["pages"]),
                "tables_count": len(result["tables"]),
                "key_value_pairs_count": len(result["key_value_pairs"]),
                "entities_count": len(result["entities"]),
                "summary": {
                    "main_text": result["content"][:1000] + "..." if len(result["content"]) > 1000 else result["content"],
                    "key_data": result["key_value_pairs"][:10],  # First 10 key-value pairs
                    "table_data": result["tables"][:3] if result["tables"] else [],  # First 3 tables
                    "detected_languages": result["languages"]
                },
                "metadata": {
                    "has_tables": len(result["tables"]) > 0,
                    "has_handwriting": any(style.get("is_handwritten", False) for style in result["styles"]),
                    "page_dimensions": [{"page": p["page_number"], "width": p["width"], "height": p["height"]} for p in result["pages"]]
                }
            }
            
            return structured_data
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "text_content": "",
                "total_pages": 0,
                "tables_count": 0,
                "key_value_pairs_count": 0,
                "entities_count": 0
            }
    
    async def get_document_summary(self, document_content: bytes) -> Dict[str, Any]:
        """
        Get a comprehensive summary of the document
        
        Args:
            document_content: The document content in bytes
            
        Returns:
            dict: Document summary
        """
        try:
            analysis = await self.extract_structured_data(document_content)
            
            if not analysis["success"]:
                return analysis
            
            # Create summary
            summary = {
                "success": True,
                "document_type": "PDF Document",  # Could be enhanced to detect type
                "total_pages": analysis["total_pages"],
                "content_preview": analysis["summary"]["main_text"],
                "has_tables": analysis["metadata"]["has_tables"],
                "tables_count": analysis["tables_count"],
                "key_information": analysis["summary"]["key_data"],
                "languages": analysis["summary"]["detected_languages"],
                "file_characteristics": {
                    "has_structured_data": analysis["key_value_pairs_count"] > 0,
                    "has_tabular_data": analysis["tables_count"] > 0,
                    "has_handwritten_content": analysis["metadata"]["has_handwriting"],
                    "estimated_words": len(analysis["text_content"].split()) if analysis["text_content"] else 0
                }
            }
            
            return summary
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error generating document summary: {str(e)}"
            }