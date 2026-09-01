from fastapi import APIRouter, File, UploadFile, HTTPException, status
from pydantic import BaseModel
import logging

from core.document_parser import DocumentParser
from core.vector_store import global_vector_store
from organization.schemas import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter()

class DocumentUploadResponse(BaseModel):
    filename: str
    chunks_processed: int
    message: str

@router.post("/documents/upload", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document (PDF, CSV, Excel, TXT), parse it into chunks, and store in FAISS Vector DB for agent retrieval.
    """
    try:
        file_bytes = await file.read()
        
        # Parse the document into chunks
        chunks = DocumentParser.parse_document(
            file_bytes=file_bytes,
            filename=file.filename,
            content_type=file.content_type
        )
        
        if not chunks:
            raise HTTPException(status_code=400, detail="Could not extract any text from the document.")
            
        # Add chunks to the Vector Store (FAISS)
        global_vector_store.add_documents(chunks)
        
        return APIResponse(
            success=True,
            data={
                "filename": file.filename,
                "chunks_processed": len(chunks),
                "message": f"Successfully processed and embedded {len(chunks)} chunks into vector memory."
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing document upload: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}")
