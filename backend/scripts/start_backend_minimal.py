"""
Start backend with minimal dependencies for API testing
This mocks MongoDB and RabbitMQ connections to allow testing without those services
"""
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock MongoDB connection
class MockMongoDBConnection:
    def __init__(self):
        self.client = None
    
    async def connect(self):
        print("Mock MongoDB connection - skipping actual connection")
        
    async def close(self):
        print("Mock MongoDB connection closed")
    
    @property
    def db(self):
        class MockDB:
            async def create_index(self, *args, **kwargs):
                pass
            async def find_one(self, *args, **kwargs):
                return None
            async def find(self, *args, **kwargs):
                return []
            async def insert_one(self, *args, **kwargs):
                class MockResult:
                    inserted_id = "mock_id"
                return MockResult()
        return MockDB()

# Mock RabbitMQ connection
class MockRabbitMQConnection:
    def __init__(self):
        self.connection = None
    
    async def connect(self):
        print("Mock RabbitMQ connection - skipping actual connection")
        
    async def close(self):
        print("Mock RabbitMQ connection closed")

# Replace the connections
import core.mongodb
import core.rabbitmq
core.mongodb.mongodb_connection = MockMongoDBConnection()
core.rabbitmq.rabbitmq_connection = MockRabbitMQConnection()

# Start the main application
if __name__ == "__main__":
    import uvicorn
    print("Starting backend with minimal dependencies...")
    print("MongoDB and RabbitMQ are mocked for testing")
    print("Access Swagger UI at: http://127.0.0.1:8000/docs")
    print("Press CTRL+C to stop the server")
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
