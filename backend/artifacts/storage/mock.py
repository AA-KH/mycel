from typing import Dict, Any
import os

from .base import StorageProvider

class MockStorageProvider(StorageProvider):
    """
    Safe mock provider for unit tests and local execution.
    Does not interact with the internet.
    """
    async def upload(self, file_path: str, destination_path: str, resource_type: str = "auto") -> Dict[str, Any]:
        import shutil
        size = 1024
        
        # Save to a local_storage folder so the user can see the generated images
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        local_dir = os.path.join(base_dir, "local_storage")
        os.makedirs(local_dir, exist_ok=True)
        
        # Flatten the destination path for simple local storage
        safe_filename = destination_path.replace("/", "_")
        local_dest = os.path.join(local_dir, safe_filename)
        
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            shutil.copy2(file_path, local_dest)
            
        return {
            "storage_key": f"mock_{destination_path}",
            "url": f"file:///{local_dest.replace(chr(92), '/')}",
            "secure_url": None,
            "format": "local_mock",
            "size_bytes": size
        }
        
    async def delete(self, storage_key: str, resource_type: str = "auto") -> bool:
        return True

    async def exists(self, storage_key: str, resource_type: str = "auto") -> bool:
        return True
