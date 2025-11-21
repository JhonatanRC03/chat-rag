import io
import uuid
from typing import Optional
from azure.storage.blob import BlobServiceClient
from app.core.config import settings


class AzureBlobStorageHelper:
    """Helper class for Azure Blob Storage operations"""
    
    def __init__(self):
        self.account_name = settings.AZURE_STORAGE_ACCOUNT_NAME
        self.account_key = settings.AZURE_STORAGE_ACCOUNT_KEY
        self.container_name = settings.AZURE_STORAGE_CONTAINER_NAME
        
        # Initialize the BlobServiceClient
        account_url = f"https://{self.account_name}.blob.core.windows.net"
        self.blob_service_client = BlobServiceClient(
            account_url=account_url,
            credential=self.account_key
        )
    
    async def upload_file(
        self, 
        file_content: bytes, 
        filename: str, 
        content_type: str = "application/pdf"
    ) -> dict:
        """
        Upload a file to Azure Blob Storage
        
        Args:
            file_content: The file content in bytes
            filename: Original filename
            content_type: MIME type of the file
            
        Returns:
            dict: Contains blob_name, blob_url, and other metadata
        """
        try:
            # Use original filename (will overwrite if same file is uploaded again)
            blob_name = filename
            
            # Get blob client
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, 
                blob=blob_name
            )
            
            # Upload the file
            blob_client.upload_blob(
                data=file_content,
                content_type=content_type,
                overwrite=True,
                metadata={
                    "original_filename": filename,
                    "content_type": content_type
                }
            )
            
            # Get blob URL
            blob_url = blob_client.url
            
            return {
                "success": True,
                "blob_name": blob_name,
                "blob_url": blob_url,
                "original_filename": filename,
                "container_name": self.container_name,
                "size": len(file_content)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def download_file(self, blob_name: str) -> Optional[bytes]:
        """
        Download a file from Azure Blob Storage
        
        Args:
            blob_name: Name of the blob to download
            
        Returns:
            bytes: File content or None if error
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, 
                blob=blob_name
            )
            
            download_stream = blob_client.download_blob()
            return download_stream.readall()
            
        except Exception as e:
            print(f"Error downloading file {blob_name}: {e}")
            return None
    
    async def delete_file(self, blob_name: str) -> bool:
        """
        Delete a file from Azure Blob Storage
        
        Args:
            blob_name: Name of the blob to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, 
                blob=blob_name
            )
            
            blob_client.delete_blob()
            return True
            
        except Exception as e:
            print(f"Error deleting file {blob_name}: {e}")
            return False
    
    async def list_files(self) -> list:
        """
        List all files in the container
        
        Returns:
            list: List of blob information
        """
        try:
            container_client = self.blob_service_client.get_container_client(
                self.container_name
            )
            
            blobs = []
            async for blob in container_client.list_blobs(include=['metadata']):
                blobs.append({
                    "name": blob.name,
                    "size": blob.size,
                    "last_modified": blob.last_modified,
                    "content_type": blob.content_settings.content_type if blob.content_settings else None,
                    "metadata": blob.metadata
                })
            
            return blobs
            
        except Exception as e:
            print(f"Error listing files: {e}")
            return []