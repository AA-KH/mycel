from .base import StorageProvider
from .mock import MockStorageProvider
from .cloudinary import CloudinaryStorageProvider

# We can dynamically swap this depending on environment.
# For now, we will default to Cloudinary if configured, else Mock.

def get_storage_provider() -> StorageProvider:
    from core.config import settings
    if settings.cloudinary_api_key and settings.cloudinary_api_secret:
        return CloudinaryStorageProvider()
    return MockStorageProvider()
