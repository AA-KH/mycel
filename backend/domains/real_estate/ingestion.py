"""
Real Estate — Excel/CSV Ingestion with MongoDB persistence and dataset versioning.

Flow:
  Excel file → validate → normalize → IngestionJob → background task → MongoDB
"""
import logging
import uuid
from io import BytesIO
from typing import Dict

import pandas as pd

from core.mongodb import mongodb_connection
from core.config import settings
from domains.real_estate.models import (
    IngestionJob, IngestionStatus, PropertyRecord
)
import google.generativeai as genai
import pymupdf

logger = logging.getLogger(__name__)

COLLECTION_PROPERTIES = settings.re_collection_properties
COLLECTION_INGESTION_JOBS = settings.re_collection_ingestion_jobs

# In-memory fallback (used when MongoDB is not available)
_mock_property_db: list = []
_ingestion_jobs: Dict[str, IngestionJob] = {}

# In-memory vector store for super-fast low-latency Voice RAG
_KNOWLEDGE_CHUNKS: list = []


def get_mock_db():
    """Return in-memory property list for use when MongoDB is unavailable."""
    return _mock_property_db


async def get_properties_collection():
    """Return MongoDB collection or None if not connected."""
    try:
        db = mongodb_connection.db
        return db[COLLECTION_PROPERTIES]
    except RuntimeError:
        return None


async def search_properties(
    budget_max: float = None,
    bhk: int = None,
    location: str = None,
    limit: int = 20,
    skip: int = 0
) -> list:
    """
    Search properties using structured filters.
    Uses MongoDB if available, falls back to in-memory mock.
    """
    col = await get_properties_collection()

    if col is not None:
        # Build MongoDB query — deterministic, no LLM
        query: Dict = {}
        if budget_max is not None:
            query["price"] = {"$lte": budget_max}
        if bhk is not None:
            query["bhk"] = bhk
        if location:
            query["$or"] = [
                {"location": {"$regex": location, "$options": "i"}},
                {"city": {"$regex": location, "$options": "i"}},
                {"locality": {"$regex": location, "$options": "i"}},
            ]

        cursor = col.find(query, {"_id": 0}).skip(skip).limit(limit)
        results = await cursor.to_list(length=limit)
        return results
    else:
        # Fallback: filter in-memory mock
        results = []
        for prop in _mock_property_db:
            d = prop if isinstance(prop, dict) else prop.model_dump()
            if budget_max is not None and d.get("price") and d["price"] > budget_max:
                continue
            if bhk is not None and d.get("bhk") and d["bhk"] != bhk:
                continue
            if location and location.lower() not in str(d.get("location", "")).lower():
                if location.lower() not in str(d.get("city", "")).lower():
                    continue
            results.append(d)
        return results[:limit]


async def compare_properties(property_ids: list) -> list:
    """Return full property records for given IDs."""
    col = await get_properties_collection()
    if col is not None:
        cursor = col.find({"property_id": {"$in": property_ids}}, {"_id": 0})
        return await cursor.to_list(length=len(property_ids))
    else:
        return [
            p.model_dump() if hasattr(p, "model_dump") else p
            for p in _mock_property_db
            if (p.property_id if hasattr(p, "property_id") else p.get("property_id")) in property_ids
        ]


async def process_property_excel(file_content: bytes, filename: str = "upload.xlsx") -> str:
    """
    Background task: parse Excel, validate, persist to MongoDB with job tracking.
    """
    global _mock_property_db

    job = IngestionJob(filename=filename)
    _ingestion_jobs[job.dataset_id] = job
    job.status = IngestionStatus.PROCESSING

    try:
        df = pd.read_excel(BytesIO(file_content), engine="openpyxl")
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
        job.schema_fields = list(df.columns)

        col = await get_properties_collection()
        records_added = 0
        rows_failed = 0

        for _, row in df.iterrows():
            try:
                data = row.to_dict()

                # Normalize amenities
                if "amenities" in data and isinstance(data["amenities"], str):
                    data["amenities"] = [a.strip() for a in data["amenities"].split(",")]
                else:
                    data["amenities"] = []

                # Replace NaN with None
                clean = {k: (None if (isinstance(v, float) and pd.isna(v)) else v) for k, v in data.items()}

                # Ensure property_id
                if not clean.get("property_id"):
                    clean["property_id"] = str(uuid.uuid4())
                else:
                    clean["property_id"] = str(clean["property_id"])

                # Generate Embedding using Gemini
                try:
                    if settings.gemini_api_key:
                        genai.configure(api_key=settings.gemini_api_key)
                        
                        # Create a dense string representing the property
                        embed_text = f"Title: {clean.get('title', '')}. " \
                                     f"Description: {clean.get('description', '')}. " \
                                     f"Location: {clean.get('location', '')} {clean.get('city', '')} {clean.get('locality', '')}. " \
                                     f"Amenities: {', '.join(clean.get('amenities', []))}."
                        
                        response = genai.embed_content(
                            model="models/gemini-embedding-2",
                            content=embed_text,
                            task_type="retrieval_document"
                        )
                        clean["embedding"] = response["embedding"]
                except Exception as e:
                    logger.warning(f"Failed to generate embedding for {clean.get('property_id')}: {e}")

                record = PropertyRecord(**clean)

                if col is not None:
                    # Upsert by property_id
                    await col.update_one(
                        {"property_id": record.property_id},
                        {"$set": record.model_dump()},
                        upsert=True
                    )
                else:
                    _mock_property_db.append(record)

                records_added += 1
            except Exception as e:
                logger.warning(f"Skipping row due to error: {e}")
                rows_failed += 1

        job.row_count = records_added
        job.rows_failed = rows_failed
        job.status = IngestionStatus.COMPLETED
        logger.info(f"Ingestion complete: {records_added} properties, {rows_failed} failed rows.")
        return job.dataset_id

    except Exception as e:
        job.status = IngestionStatus.FAILED
        job.error_detail = str(e)
        logger.error(f"Ingestion failed: {e}")
        raise


def get_ingestion_job(dataset_id: str) -> IngestionJob:
    return _ingestion_jobs.get(dataset_id)


def get_all_ingestion_jobs() -> list:
    return [j.model_dump() for j in sorted(
        _ingestion_jobs.values(),
        key=lambda x: x.uploaded_at,
        reverse=True
    )]


async def process_knowledge_document(file_content: bytes, filename: str) -> int:
    """
    Parse a document (PDF or Text), chunk it, generate embeddings, and store in-memory.
    Returns the number of chunks processed.
    """
    global _KNOWLEDGE_CHUNKS
    
    text = ""
    if filename.lower().endswith('.pdf'):
        try:
            # Use pymupdf directly to avoid deprecation warnings from fitz
            doc = pymupdf.open(stream=file_content, filetype="pdf")
            for page in doc:
                text += page.get_text() + "\n"
        except Exception as e:
            logger.error(f"Failed to parse PDF {filename}: {e}")
            raise
    elif filename.lower().endswith('.xlsx') or filename.lower().endswith('.xls') or filename.lower().endswith('.csv'):
        try:
            import io
            if filename.lower().endswith('.csv'):
                import pandas as pd
                df = pd.read_csv(io.BytesIO(file_content))
                for index, row in df.iterrows():
                    row_text = " | ".join([f"{col}: {val}" for col, val in row.items() if not pd.isna(val)])
                    text += row_text + "\n"
            else:
                try:
                    from python_calamine import CalamineWorkbook
                    wb = CalamineWorkbook.from_filelike(io.BytesIO(file_content))
                    for sheet_name in wb.sheet_names:
                        sheet = wb.get_sheet_by_name(sheet_name)
                        for row in sheet.to_python():
                            row_text = " | ".join([str(cell) for cell in row if cell is not None and str(cell).strip()])
                            if row_text:
                                text += row_text + "\n"
                except Exception as cal_err:
                    logger.warning(f"Failed to read with calamine, trying fallbacks for {filename}: {cal_err}")
                    file_content.seek(0) if hasattr(file_content, 'seek') else None
                    import pandas as pd
                    try:
                        df = pd.read_csv(io.BytesIO(file_content), encoding='utf-8')
                    except UnicodeDecodeError:
                        file_content.seek(0) if hasattr(file_content, 'seek') else None
                        try:
                            df = pd.read_csv(io.BytesIO(file_content), encoding='cp1252')
                        except Exception:
                            # It might be an HTML table saved with an .xlsx extension
                            file_content.seek(0) if hasattr(file_content, 'seek') else None
                            dfs = pd.read_html(io.BytesIO(file_content))
                            df = dfs[0] if dfs else pd.DataFrame()
                    
                    for index, row in df.iterrows():
                        row_text = " | ".join([f"{col}: {val}" for col, val in row.items() if not pd.isna(val)])
                        text += row_text + "\n"
        except Exception as e:
            logger.error(f"Failed to parse tabular file {filename}: {e}")
            raise
    else:
        # Fallback to plain text
        text = file_content.decode('utf-8', errors='ignore')
    
    # Chunking: split text into 500 character chunks with 50 overlap
    chunk_size = 500
    overlap = 50
    
    chunks = []
    i = 0
    while i < len(text):
        end = min(i + chunk_size, len(text))
        chunks.append(text[i:end].strip())
        i += chunk_size - overlap
        if i >= len(text) - overlap:
            break
            
    # Filter empty chunks
    chunks = [c for c in chunks if len(c) > 10]
    
    # Cap chunks to prevent API rate limits / infinite hangs on huge datasets
    max_chunks = 500
    if len(chunks) > max_chunks:
        logger.warning(f"File {filename} is too large. Truncating to {max_chunks} chunks.")
        chunks = chunks[:max_chunks]
    
    if not chunks:
        logger.warning(f"No text extracted from {filename}")
        return 0
        
    # Configure genai and generate embeddings
    if settings.gemini_api_key:
        genai.configure(api_key=settings.gemini_api_key)
    else:
        logger.warning("Gemini API key not configured, cannot embed knowledge.")
        return 0
        
    chunks_added = 0
    batch_size = 50
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        try:
            response = genai.embed_content(
                model="models/gemini-embedding-2",
                content=batch,
                task_type="retrieval_document"
            )
            
            embeddings = response["embedding"]
            for j, embedding in enumerate(embeddings):
                _KNOWLEDGE_CHUNKS.append({
                    "doc_id": f"{filename}-{i+j}",
                    "title": filename,
                    "content": batch[j],
                    "embedding": embedding
                })
                chunks_added += 1
        except Exception as e:
            logger.error(f"Failed to embed batch {i} of {filename}: {e}")
            
    logger.info(f"Processed knowledge doc {filename}: {chunks_added} chunks embedded.")
    return chunks_added

