import shutil
import uuid
import logging
from pathlib import Path
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Query
from app.config import settings
from app.db import get_db_connection
from app.services.pipeline import ProcessingPipeline
from app.models import DocumentSummary

router = APIRouter(prefix="/api/documents", tags=["Documents"])
logger = logging.getLogger(__name__)

pipeline = ProcessingPipeline()

@router.get("", response_model=List[DocumentSummary])
def list_documents():
    """Lists all registered documents with fact counts and processing status."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT d.id, d.filename, d.filesize, d.page_count, d.dataset_tag, d.status, d.summary, d.created_at,
               COALESCE(d.processed_pages, 0) as processed_pages,
               COALESCE(d.total_pages, 0) as total_pages,
               COALESCE(d.current_step, '') as current_step,
               COALESCE(d.progress_pct, 0) as progress_pct,
               COUNT(f.id) as fact_count
        FROM documents d
        LEFT JOIN facts f ON d.id = f.document_id
        GROUP BY d.id
        ORDER BY d.created_at DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    
    return [
        DocumentSummary(
            id=r["id"],
            filename=r["filename"],
            filesize=r["filesize"],
            page_count=r["page_count"],
            dataset_tag=r["dataset_tag"],
            status=r["status"],
            summary=r["summary"] or "",
            fact_count=r["fact_count"],
            processed_pages=r["processed_pages"],
            total_pages=r["total_pages"],
            current_step=r["current_step"],
            progress_pct=r["progress_pct"],
            created_at=str(r["created_at"])
        ) for r in rows
    ]

@router.get("/{doc_id}")
def get_document(doc_id: str):
    """Retrieves document detail, including extracted facts and pages."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
    doc = cursor.fetchone()
    if not doc:
        conn.close()
        raise HTTPException(status_code=404, detail="Document not found")
        
    cursor.execute("SELECT * FROM facts WHERE document_id = ? ORDER BY page_number ASC", (doc_id,))
    facts = [dict(f) for f in cursor.fetchall()]
    
    cursor.execute("SELECT id, page_number, char_count, table_count FROM document_pages WHERE document_id = ? ORDER BY page_number ASC", (doc_id,))
    pages = [dict(p) for p in cursor.fetchall()]
    conn.close()
    
    return {
        "document": dict(doc),
        "facts": facts,
        "pages": pages
    }

@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """
    Accepts new PDF uploads and triggers background text extraction,
    fact extraction, and incremental reconciliation against existing knowledge.
    Enforces a 50MB file size limit.
    """
    safe_filename = Path(file.filename).name
    if not safe_filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    doc_id = f"doc-{uuid.uuid4().hex[:8]}"
    upload_path = settings.UPLOAD_DIR / f"{doc_id}_{safe_filename}"
    
    total_size = 0
    try:
        with open(upload_path, "wb") as buffer:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                total_size += len(chunk)
                if total_size > MAX_FILE_SIZE:
                    buffer.close()
                    if upload_path.exists():
                        upload_path.unlink()
                    raise HTTPException(status_code=413, detail="File size exceeds maximum permitted limit (50 MB).")
                buffer.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        if upload_path.exists():
            upload_path.unlink()
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}")

    # Ingest in background
    background_tasks.add_task(pipeline.ingest_pdf, upload_path, "user-upload", doc_id)

    return {
        "message": f"File '{file.filename}' uploaded successfully. Processing started.",
        "document_id": doc_id,
        "filename": file.filename,
        "status": "processing"
    }

@router.delete("/{doc_id}")
def delete_document(doc_id: str):
    """Deletes a document and cascades to its facts, pages, relationships, and disk file."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT filepath FROM documents WHERE id = ?", (doc_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Document not found")
    
    filepath = row["filepath"]
    if filepath and Path(filepath).exists():
        try:
            Path(filepath).unlink()
        except Exception as e:
            logger.warning(f"Could not unlink file {filepath}: {e}")

    cursor.execute("DELETE FROM relationships WHERE doc_id_1 = ? OR doc_id_2 = ?", (doc_id, doc_id))
    cursor.execute("DELETE FROM facts WHERE document_id = ?", (doc_id,))
    cursor.execute("DELETE FROM document_pages WHERE document_id = ?", (doc_id,))
    cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()
    return {"message": f"Document {doc_id} deleted successfully."}
