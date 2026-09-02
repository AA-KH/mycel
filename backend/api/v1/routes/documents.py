from fastapi import APIRouter, File, UploadFile, HTTPException, status, Form
from pydantic import BaseModel
import logging
import cloudinary.uploader

from core.rabbitmq import rabbitmq_producer
from organization.schemas import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter()

class DocumentUploadResponse(BaseModel):
    filename: str
    chunks_processed: int
    message: str

@router.post("/documents/upload", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    project_id: str = Form("draft")
):
    """
    Upload a document (PDF, CSV, Excel, TXT), store it in Cloudinary, and enqueue an ingestion job via RabbitMQ.
    """
    try:
        file_bytes = await file.read()
        
        # Upload to Cloudinary
        upload_result = cloudinary.uploader.upload(
            file_bytes,
            resource_type="raw",
            public_id=f"mycel/{project_id}/{file.filename}",
            type="private"
        )
        
        cloudinary_url = upload_result.get("secure_url")
        if not cloudinary_url:
            raise Exception("Failed to get secure_url from Cloudinary")
            
        # Queue ingestion task
        event_payload = {
            "project_id": project_id,
            "filename": file.filename,
            "content_type": file.content_type,
            "cloudinary_url": cloudinary_url
        }
        
        await rabbitmq_producer.publish("document.ingest", event_payload)
        
        return APIResponse(
            success=True,
            data={
                "filename": file.filename,
                "cloudinary_url": cloudinary_url,
                "message": "File uploaded and ingestion job queued."
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing document upload: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")
