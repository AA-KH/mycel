from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class StorageProvider(ABC):
    """
    Interface for Artifact Storage Providers (Cloudinary, S3, Local, etc.).
    """
    
    @abstractmethod
    async def upload(self, file_path: str, destination_path: str, resource_type: str = "auto") -> Dict[str, Any]:
        """
        Uploads a local file to the storage provider.
        Returns a dict containing standard provider metadata:
        - storage_key / public_id
        - url
        - secure_url
        - format
        - size_bytes
        """
        pass
        
    @abstractmethod
    async def delete(self, storage_key: str, resource_type: str = "auto") -> bool:
        """
        Deletes the file from the storage provider.
        """
        pass

    @abstractmethod
    async def exists(self, storage_key: str, resource_type: str = "auto") -> bool:
        """
        Checks if the file exists.
        """
        pass
