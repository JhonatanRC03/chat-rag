import uuid
from openai import AzureOpenAI
from typing import List, Dict, Any, Optional
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from app.core.config import settings
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    ComplexField,
    VectorSearch,
    VectorSearchProfile,
    VectorSearchAlgorithmConfiguration,
    HnswAlgorithmConfiguration
)

class AzureAISearchHelper:
    """Helper class for Azure AI Search operations"""
    
    def __init__(self):
        self.service_name = settings.AZURE_SEARCH_SERVICE
        self.api_key = settings.AZURE_SEARCH_API_KEY
        self.index_name = settings.AZURE_SEARCH_INDEX_NAME
        
        # Initialize credentials
        self.credential = AzureKeyCredential(self.api_key)
        
        # Initialize clients
        self.search_client = SearchClient(
            endpoint=f"https://{self.service_name}.search.windows.net",
            index_name=self.index_name,
            credential=self.credential
        )
        
        self.index_client = SearchIndexClient(
            endpoint=f"https://{self.service_name}.search.windows.net",
            credential=self.credential
        )
    
    async def generate_embeddings(self, text: str) -> List[float]:
        """
        Generate embeddings using OpenAI ada-002 model
        
        Args:
            text: Text to generate embeddings for
            
        Returns:
            list: Embedding vectors
        """
        try:
            # Truncate text if too long (ada-002 has token limits)
            if len(text) > 8000:  # Conservative limit
                text = text[:8000]
            
            # Initialize Azure OpenAI client
            client = AzureOpenAI(
                api_key=settings.AZURE_OPENAI_API_KEY,
                api_version="2024-02-01",
                azure_endpoint=settings.AZURE_OPENAI_ENDPOINT
            )
            
            response = client.embeddings.create(
                model=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                input=text
            )
            
            return response.data[0].embedding
            
        except Exception as e:
            print(f"Error generating embeddings: {e}")
            return []
    
    async def create_document_index(self) -> bool:
        """
        Create the search index for documents if it doesn't exist
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            
            # Define simplified index schema - solo campos necesarios
            fields = [
                SimpleField(name="id", type=SearchFieldDataType.String, key=True),
                SearchableField(name="content", type=SearchFieldDataType.String),
                SimpleField(name="category", type=SearchFieldDataType.String),
                SimpleField(name="sourcepage", type=SearchFieldDataType.String),
                SimpleField(name="sourcefile", type=SearchFieldDataType.String),
                SimpleField(name="storageUrl", type=SearchFieldDataType.String),
                SimpleField(name="company", type=SearchFieldDataType.String),
                SearchField(
                    name="embedding3",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    searchable=True,
                    vector_search_dimensions=1536,  # ada-002 dimensions
                    vector_search_profile_name="my-vector-config"
                )
            ]
            
            # Configure vector search
            vector_search = VectorSearch(
                profiles=[
                    VectorSearchProfile(
                        name="my-vector-config",
                        algorithm_configuration_name="my-hnsw"
                    )
                ],
                algorithms=[
                    HnswAlgorithmConfiguration(
                        name="my-hnsw"
                    )
                ]
            )
            
            # Create the index with vector search
            index = SearchIndex(
                name=self.index_name, 
                fields=fields,
                vector_search=vector_search
            )
            
            # Check if index exists, if not create it
            try:
                self.index_client.get_index(self.index_name)
                print(f"Index {self.index_name} already exists")
                return True
            except:
                result = self.index_client.create_index(index)
                print(f"Index {self.index_name} created successfully")
                return True
                
        except Exception as e:
            print(f"Error creating index: {e}")
            return False
    
    async def index_document(
        self, 
        document_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Index a document in Azure AI Search with embeddings
        
        Args:
            document_data: Dictionary containing document information
            
        Returns:
            dict: Result of the indexing operation
        """
        try:
            # Ensure document has required fields
            if "id" not in document_data:
                document_data["id"] = str(uuid.uuid4())
            
            # Generate embeddings for the content
            content_text = document_data.get("content", "")
            if content_text.strip():
                embeddings = await self.generate_embeddings(content_text)
                if embeddings:
                    document_data["embedding3"] = embeddings
            
            # Upload document to search index
            result = self.search_client.upload_documents([document_data])
            
            return {
                "success": True,
                "document_id": document_data["id"],
                "result": result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def search_documents(
        self, 
        query: str, 
        top: int = 10,
        filters: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search documents in the index
        
        Args:
            query: Search query
            top: Number of results to return
            filters: Optional OData filter expression
            
        Returns:
            dict: Search results
        """
        try:
            results = self.search_client.search(
                search_text=query,
                top=top,
                filter=filters,
                include_total_count=True,
                highlight_fields="content,extracted_text"
            )
            
            documents = []
            for result in results:
                doc = dict(result)
                documents.append(doc)
            
            return {
                "success": True,
                "documents": documents,
                "count": len(documents)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "documents": [],
                "count": 0
            }
    
    async def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific document by ID
        
        Args:
            document_id: The document ID
            
        Returns:
            dict: Document data or None if not found
        """
        try:
            result = self.search_client.get_document(key=document_id)
            return dict(result)
            
        except Exception as e:
            print(f"Error getting document {document_id}: {e}")
            return None
    
    async def update_document(
        self, 
        document_id: str, 
        document_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update an existing document
        
        Args:
            document_id: The document ID
            document_data: Updated document data
            
        Returns:
            dict: Result of the update operation
        """
        try:
            document_data["id"] = document_id
            result = self.search_client.merge_or_upload_documents([document_data])
            
            return {
                "success": True,
                "document_id": document_id,
                "result": result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_document(self, document_id: str) -> bool:
        """
        Delete a document from the index
        
        Args:
            document_id: The document ID to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            result = self.search_client.delete_documents([{"id": document_id}])
            return True
            
        except Exception as e:
            print(f"Error deleting document {document_id}: {e}")
            return False
    
    async def suggest_documents(
        self, 
        query: str, 
        suggester_name: str = "sg"
    ) -> List[str]:
        """
        Get search suggestions
        
        Args:
            query: Partial query for suggestions
            suggester_name: Name of the suggester
            
        Returns:
            list: List of suggestions
        """
        try:
            results = self.search_client.suggest(
                search_text=query,
                suggester_name=suggester_name
            )
            
            suggestions = []
            for result in results:
                suggestions.append(result["text"])
            
            return suggestions
            
        except Exception as e:
            print(f"Error getting suggestions: {e}")
            return []