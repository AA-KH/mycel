import io
import fitz  # PyMuPDF
import pandas as pd
from typing import List, Dict

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks of roughly `chunk_size` words."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks

class DocumentParser:
    @staticmethod
    def parse_pdf(file_bytes: bytes, filename: str) -> List[Dict[str, str]]:
        """Extracts text from PDF and returns a list of chunks with metadata."""
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        chunks = []
        for page_num, page in enumerate(doc):
            text = page.get_text("text")
            if text.strip():
                page_chunks = chunk_text(text)
                for i, chunk in enumerate(page_chunks):
                    chunks.append({
                        "text": chunk,
                        "source": filename,
                        "metadata": f"Page {page_num + 1}, Part {i + 1}"
                    })
        return chunks

    @staticmethod
    def parse_csv(file_bytes: bytes, filename: str) -> List[Dict[str, str]]:
        """Extracts text from CSV by converting rows to readable sentences."""
        df = pd.read_csv(io.BytesIO(file_bytes))
        # Convert DataFrame to a string representation, chunking every 50 rows
        chunks = []
        chunk_size = 50
        for i in range(0, len(df), chunk_size):
            chunk_df = df.iloc[i:i + chunk_size]
            text = chunk_df.to_csv(index=False)
            chunks.append({
                "text": text,
                "source": filename,
                "metadata": f"Rows {i + 1} to {i + len(chunk_df)}"
            })
        return chunks

    @staticmethod
    def parse_excel(file_bytes: bytes, filename: str) -> List[Dict[str, str]]:
        """Extracts text from Excel by converting sheets and rows to readable text."""
        chunks = []
        excel_file = pd.ExcelFile(io.BytesIO(file_bytes))
        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name)
            chunk_size = 50
            for i in range(0, len(df), chunk_size):
                chunk_df = df.iloc[i:i + chunk_size]
                text = f"Sheet: {sheet_name}\n" + chunk_df.to_csv(index=False)
                chunks.append({
                    "text": text,
                    "source": filename,
                    "metadata": f"Sheet '{sheet_name}', Rows {i + 1} to {i + len(chunk_df)}"
                })
        return chunks

    @classmethod
    def parse_document(cls, file_bytes: bytes, filename: str, content_type: str) -> List[Dict[str, str]]:
        """Route to the correct parser based on filename or content type."""
        filename_lower = filename.lower()
        if filename_lower.endswith(".pdf") or "pdf" in content_type:
            return cls.parse_pdf(file_bytes, filename)
        elif filename_lower.endswith(".csv") or "csv" in content_type:
            return cls.parse_csv(file_bytes, filename)
        elif filename_lower.endswith(".xlsx") or filename_lower.endswith(".xls") or "excel" in content_type or "spreadsheet" in content_type:
            return cls.parse_excel(file_bytes, filename)
        else:
            # Fallback: Treat as plain text
            text = file_bytes.decode("utf-8", errors="ignore")
            text_chunks = chunk_text(text)
            return [
                {
                    "text": chunk,
                    "source": filename,
                    "metadata": f"Part {i + 1}"
                }
                for i, chunk in enumerate(text_chunks)
            ]
