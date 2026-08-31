"""
Base Repository Pattern.
Provides generic MongoDB CRUD operations for standard Mycel entities.
"""

from typing import Any, Dict, List, Optional, TypeVar, Generic
from pydantic import BaseModel
from bson import ObjectId

from core.errors import DatabaseError

T = TypeVar("T", bound=BaseModel)

class BaseRepository(Generic[T]):
    """
    Abstract base repository for MongoDB collections.
    """
    
    def __init__(self, db, collection_name: str, model_class: type[T]):
        self.db = db
        self.collection = db[collection_name]
        self.model_class = model_class

    def _serialize_id(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB _id to string id."""
        if document and "_id" in document:
            document["id"] = str(document.pop("_id"))
        return document

    async def get_by_id(self, entity_id: str) -> Optional[T]:
        """Fetch a single entity by its ID."""
        try:
            if not ObjectId.is_valid(entity_id):
                return None
                
            document = await self.collection.find_one({"_id": ObjectId(entity_id)})
            if not document:
                return None
                
            return self.model_class(**self._serialize_id(document))
        except Exception as e:
            raise DatabaseError(f"Failed to fetch {self.collection.name} by ID", details={"error": str(e)})

    async def create(self, entity: T) -> T:
        """Create a new entity in the collection."""
        try:
            document = entity.model_dump(by_alias=True, exclude={"id"}, exclude_none=True)
            result = await self.collection.insert_one(document)
            
            # Fetch the created document to ensure full representation
            created = await self.collection.find_one({"_id": result.inserted_id})
            return self.model_class(**self._serialize_id(created))
        except Exception as e:
            raise DatabaseError(f"Failed to create {self.collection.name}", details={"error": str(e)})

    async def update(self, entity_id: str, update_data: Dict[str, Any]) -> Optional[T]:
        """Update an existing entity."""
        try:
            if not ObjectId.is_valid(entity_id):
                return None
                
            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(entity_id)},
                {"$set": update_data},
                return_document=True
            )
            
            if not result:
                return None
                
            return self.model_class(**self._serialize_id(result))
        except Exception as e:
            raise DatabaseError(f"Failed to update {self.collection.name}", details={"error": str(e)})

    async def delete(self, entity_id: str) -> bool:
        """Delete an entity by ID."""
        try:
            if not ObjectId.is_valid(entity_id):
                return False
                
            result = await self.collection.delete_one({"_id": ObjectId(entity_id)})
            return result.deleted_count > 0
        except Exception as e:
            raise DatabaseError(f"Failed to delete {self.collection.name}", details={"error": str(e)})

    async def find(self, query: Dict[str, Any], limit: int = 100, skip: int = 0) -> List[T]:
        """Find entities matching a query."""
        try:
            cursor = self.collection.find(query).skip(skip).limit(limit)
            documents = await cursor.to_list(length=limit)
            return [self.model_class(**self._serialize_id(doc)) for doc in documents]
        except Exception as e:
            raise DatabaseError(f"Failed to query {self.collection.name}", details={"error": str(e)})
