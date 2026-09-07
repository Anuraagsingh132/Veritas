import json
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from app.db import get_db_connection
from app.models import FactResponse

router = APIRouter(prefix="/api/facts", tags=["Facts"])

@router.get("", response_model=List[FactResponse])
def list_facts(
    doc_id: Optional[str] = Query(None, description="Filter by document ID"),
    category: Optional[str] = Query(None, description="Filter by fact category"),
    q: Optional[str] = Query(None, description="Keyword search across subject/value/quote"),
    failures_only: bool = Query(False, description="Filter for extraction failure cases")
):
    """
    Queries facts with multi-criteria filtering and full-text keyword matching.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT f.*, d.filename as document_filename
        FROM facts f
        JOIN documents d ON f.document_id = d.id
        WHERE 1=1
    """
    params = []
    
    if doc_id:
        query += " AND f.document_id = ?"
        params.append(doc_id)
        
    if category:
        query += " AND f.category = ?"
        params.append(category)
        
    if failures_only:
        query += " AND f.is_failure_example = 1"
        
    if q:
        query += " AND (f.subject LIKE ? OR f.value LIKE ? OR f.exact_quote LIKE ? OR f.predicate LIKE ?)"
        like_term = f"%{q}%"
        params.extend([like_term, like_term, like_term, like_term])
        
    query += " ORDER BY f.created_at DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [
        FactResponse(
            id=r["id"],
            document_id=r["document_id"],
            document_filename=r["document_filename"],
            page_number=r["page_number"],
            category=r["category"],
            subject=r["subject"],
            predicate=r["predicate"],
            value=r["value"],
            unit=r["unit"] or "",
            temporal_context=r["temporal_context"] or "",
            scope_context=r["scope_context"] or "",
            exact_quote=r["exact_quote"],
            char_offset_start=r["char_offset_start"],
            char_offset_end=r["char_offset_end"],
            confidence=r["confidence"],
            is_failure_example=bool(r["is_failure_example"]),
            failure_notes=r["failure_notes"] or "",
            bbox=json.loads(r["bbox"]) if ("bbox" in r.keys() and r["bbox"]) else [],
            created_at=str(r["created_at"])
        ) for r in rows
    ]

@router.get("/{fact_id}")
def get_fact(fact_id: str):
    """Retrieves fact detail along with all cross-document relationships linked to it."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT f.*, d.filename as document_filename
        FROM facts f
        JOIN documents d ON f.document_id = d.id
        WHERE f.id = ?
    """, (fact_id,))
    fact = cursor.fetchone()
    if not fact:
        conn.close()
        raise HTTPException(status_code=404, detail="Fact not found")
        
    cursor.execute("""
        SELECT r.*, 
               f2.subject as other_subject, f2.value as other_value, f2.unit as other_unit, f2.exact_quote as other_quote,
               d2.filename as other_doc_filename
        FROM relationships r
        JOIN facts f2 ON (CASE WHEN r.fact_id_1 = ? THEN r.fact_id_2 ELSE r.fact_id_1 END) = f2.id
        JOIN documents d2 ON f2.document_id = d2.id
        WHERE r.fact_id_1 = ? OR r.fact_id_2 = ?
    """, (fact_id, fact_id, fact_id))
    relationships = [dict(r) for r in cursor.fetchall()]
    conn.close()
    
    return {
        "fact": dict(fact),
        "relationships": relationships
    }
