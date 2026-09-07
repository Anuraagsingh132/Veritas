from typing import List, Optional
from fastapi import APIRouter, Query
from app.db import get_db_connection
from app.services.pipeline import ProcessingPipeline
from app.models import RelationshipResponse, FactResponse

router = APIRouter(prefix="/api/reconciliation", tags=["Reconciliation"])

pipeline = ProcessingPipeline()

@router.get("", response_model=List[RelationshipResponse])
def list_relationships(
    type: Optional[str] = Query(None, description="corroboration, genuine_contradiction, contextual_reconciliation, extraction_failure"),
    case: Optional[str] = Query(None, description="Filter by case (case_1_corroboration, case_2_contradiction, etc.)"),
    limit: int = Query(100, ge=1, le=500, description="Max relationships to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """
    Retrieves cross-document reconciled relationships with both linked facts and source evidence.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT r.*,
               f1.id as f1_id, f1.document_id as f1_doc_id, f1.page_number as f1_page, f1.category as f1_cat,
               f1.subject as f1_sub, f1.predicate as f1_pred, f1.value as f1_val, f1.unit as f1_unit,
               f1.temporal_context as f1_temp, f1.scope_context as f1_scope, f1.exact_quote as f1_quote,
               f1.confidence as f1_conf, f1.is_failure_example as f1_fail, f1.failure_notes as f1_fail_notes,
               f1.created_at as f1_created, d1.filename as f1_doc_name,
               f2.id as f2_id, f2.document_id as f2_doc_id, f2.page_number as f2_page, f2.category as f2_cat,
               f2.subject as f2_sub, f2.predicate as f2_pred, f2.value as f2_val, f2.unit as f2_unit,
               f2.temporal_context as f2_temp, f2.scope_context as f2_scope, f2.exact_quote as f2_quote,
               f2.confidence as f2_conf, f2.is_failure_example as f2_fail, f2.failure_notes as f2_fail_notes,
               f2.created_at as f2_created, d2.filename as f2_doc_name
        FROM relationships r
        JOIN facts f1 ON r.fact_id_1 = f1.id
        JOIN facts f2 ON r.fact_id_2 = f2.id
        JOIN documents d1 ON f1.document_id = d1.id
        JOIN documents d2 ON f2.document_id = d2.id
        WHERE 1=1
    """
    params = []
    if type:
        query += " AND r.relationship_type = ?"
        params.append(type)
    if case:
        query += " AND r.case_category = ?"
        params.append(case)
        
    query += " ORDER BY r.created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for r in rows:
        fact_1 = FactResponse(
            id=r["f1_id"],
            document_id=r["f1_doc_id"],
            document_filename=r["f1_doc_name"],
            page_number=r["f1_page"],
            category=r["f1_cat"],
            subject=r["f1_sub"],
            predicate=r["f1_pred"],
            value=r["f1_val"],
            unit=r["f1_unit"] or "",
            temporal_context=r["f1_temp"] or "",
            scope_context=r["f1_scope"] or "",
            exact_quote=r["f1_quote"],
            confidence=r["f1_conf"],
            is_failure_example=bool(r["f1_fail"]),
            failure_notes=r["f1_fail_notes"] or "",
            created_at=str(r["f1_created"])
        )
        fact_2 = FactResponse(
            id=r["f2_id"],
            document_id=r["f2_doc_id"],
            document_filename=r["f2_doc_name"],
            page_number=r["f2_page"],
            category=r["f2_cat"],
            subject=r["f2_sub"],
            predicate=r["f2_pred"],
            value=r["f2_val"],
            unit=r["f2_unit"] or "",
            temporal_context=r["f2_temp"] or "",
            scope_context=r["f2_scope"] or "",
            exact_quote=r["f2_quote"],
            confidence=r["f2_conf"],
            is_failure_example=bool(r["f2_fail"]),
            failure_notes=r["f2_fail_notes"] or "",
            created_at=str(r["f2_created"])
        )
        results.append(RelationshipResponse(
            id=r["id"],
            fact_1=fact_1,
            fact_2=fact_2,
            relationship_type=r["relationship_type"],
            confidence=r["confidence"],
            reasoning=r["reasoning"],
            context_difference=r["context_difference"] or "",
            case_category=r["case_category"] or "",
            created_at=str(r["created_at"])
        ))
        
    return results

@router.post("/reconcile-all")
def trigger_reconciliation():
    """Triggers global pairwise reconciliation across all facts in database."""
    count = pipeline.reconcile_all_existing()
    return {"message": f"Global reconciliation completed. {count} relationships updated."}
