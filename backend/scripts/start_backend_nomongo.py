"""
Start backend without MongoDB connection for testing API endpoints
"""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock MongoDB connection to avoid connection errors
class MockMongoDBConnection:
    def __init__(self):
        self.client = None
    
    async def connect(self):
        print("Mock MongoDB connection - skipping actual connection")
        
    async def close(self):
        print("Mock MongoDB connection closed")
    
    @property
    def db(self):
        # Return a mock database object
        class MockDB:
            async def create_index(self, *args, **kwargs):
                pass
            async def find_one(self, *args, **kwargs):
                return None
            async def find(self, *args, **kwargs):
                return []
        return MockDB()

# Replace the mongodb_connection
import core.mongodb
core.mongodb.mongodb_connection = MockMongoDBConnection()

# Now start the main application
if __name__ == "__main__":
    import uvicorn
    print("Starting backend with mock MongoDB connection...")
    print("Access Swagger UI at: http://127.0.0.1:8000/docs")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
