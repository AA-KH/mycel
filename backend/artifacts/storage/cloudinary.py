import os
from typing import Dict, Any

from .base import StorageProvider
from core.config import settings

class CloudinaryStorageProvider(StorageProvider):
    """
    Integrates with Cloudinary to securely upload artifacts.
    Credentials are NEVER exposed outside of this module.
    """
    def __init__(self):
        # We only import cloudinary if we are actually using it
        try:
            import cloudinary
            import cloudinary.uploader
            import cloudinary.api
            self._cloudinary_loaded = True
            
            # Configure Cloudinary if credentials are present
            if settings.cloudinary_api_key and settings.cloudinary_api_secret:
                cloudinary.config(
                    cloud_name=settings.cloudinary_cloud_name,
                    api_key=settings.cloudinary_api_key,
                    api_secret=settings.cloudinary_api_secret
                )
            
        except ImportError:
            self._cloudinary_loaded = False
            
    async def upload(self, file_path: str, destination_path: str, resource_type: str = "auto") -> Dict[str, Any]:
        if not self._cloudinary_loaded:
            raise RuntimeError("Cloudinary library not installed.")
            
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_path} not found.")

        # Map 'document' to 'raw' resource type for Cloudinary
        if resource_type in ("document", "pdf", "text"):
            resource_type = "raw"
            
        import cloudinary.uploader
        
        # Upload using the strictly defined destination path
        response = cloudinary.uploader.upload(
            file_path,
            public_id=destination_path,
            resource_type=resource_type,
            overwrite=True
        )
        
        return {
            "storage_key": response.get("public_id"),
            "url": response.get("url"),
            "secure_url": response.get("secure_url"),
            "format": response.get("format"),
            "size_bytes": response.get("bytes", 0)
        }

    async def delete(self, storage_key: str, resource_type: str = "auto") -> bool:
        if not self._cloudinary_loaded:
            return False
            
        if resource_type in ("document", "pdf", "text"):
            resource_type = "raw"
            
        import cloudinary.uploader
        try:
            res = cloudinary.uploader.destroy(storage_key, resource_type=resource_type)
            return res.get("result") == "ok"
        except Exception:
            return False

    async def exists(self, storage_key: str, resource_type: str = "auto") -> bool:
        if not self._cloudinary_loaded:
            return False
            
        if resource_type in ("document", "pdf", "text"):
            resource_type = "raw"
            
        import cloudinary.api
        try:
            cloudinary.api.resource(storage_key, resource_type=resource_type)
            return True
        except Exception:
            return False
