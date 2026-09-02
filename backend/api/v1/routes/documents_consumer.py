import logging
import urllib.request
from typing import Dict, Any

from core.logger import logger
from core.document_parser import DocumentParser
from core.vector_store import global_vector_store
from core.mongodb import mongodb_connection

async def document_ingest_consumer(message_body: bytes, *args, **kwargs):
    """
    Consumes document.ingest events from RabbitMQ.
    Downloads the file from Cloudinary, parses it, and stores the chunks in MongoDB vector store.
    """
    import json
    data = message_body if isinstance(message_body, dict) else json.loads(message_body)
    
    project_id = data.get("project_id")
    filename = data.get("filename")
    content_type = data.get("content_type")
    cloudinary_url = data.get("cloudinary_url")
    
    if not cloudinary_url:
        logger.error(f"Missing cloudinary_url in document.ingest event: {data}")
        return
        
    logger.info(f"Starting ingestion for {filename} (Project: {project_id})")
    
    try:
        # Download file bytes
        req = urllib.request.Request(cloudinary_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            file_bytes = response.read()
            
        # Parse document
        chunks = DocumentParser.parse_document(
            file_bytes=file_bytes,
            filename=filename,
            content_type=content_type
        )
        
        if not chunks:
            logger.warning(f"No text could be extracted from {filename}")
            return
            
        # Check if project was already created while we were processing
        if project_id == "draft":
            db = mongodb_connection.db
            owning_project = await db.projects.find_one({"files": cloudinary_url})
            if owning_project:
                project_id = owning_project.get("project_id", project_id)
                logger.info(f"Resolved draft to actual project_id: {project_id}")
            
        # Insert chunks into MongoDB Vector Store
        await global_vector_store.add_documents(project_id, cloudinary_url, chunks)
        
        # Log successful ingestion
        logger.info(f"Successfully ingested {len(chunks)} chunks for {filename}")
        
    except Exception as e:
        logger.error(f"Failed to ingest document {filename}: {str(e)}", exc_info=True)
