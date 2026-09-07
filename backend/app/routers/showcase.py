import json
import logging
from fastapi import APIRouter
from app.models import ShowcaseResponse, ShowcaseCase, FactResponse
from app.db import get_db_connection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/showcase", tags=["Showcase Cases"])

def _row_to_fact_response(row_prefix: str, row) -> FactResponse:
    """Helper to convert a joined SQL row into a typed FactResponse."""
    bbox_raw = row[f"{row_prefix}_bbox"] if f"{row_prefix}_bbox" in row.keys() else "[]"
    try:
        bbox = json.loads(bbox_raw) if bbox_raw else []
    except Exception:
        bbox = []

    return FactResponse(
        id=row[f"{row_prefix}_id"],
        document_id=row[f"{row_prefix}_doc_id"],
        document_filename=row[f"{row_prefix}_doc_filename"],
        page_number=row[f"{row_prefix}_page"],
        category=row[f"{row_prefix}_category"],
        subject=row[f"{row_prefix}_subject"],
        predicate=row[f"{row_prefix}_predicate"],
        value=row[f"{row_prefix}_value"],
        unit=row[f"{row_prefix}_unit"] or "",
        temporal_context=row[f"{row_prefix}_temporal"] or "",
        scope_context=row[f"{row_prefix}_scope"] or "",
        exact_quote=row[f"{row_prefix}_quote"],
        char_offset_start=row[f"{row_prefix}_start"] or 0,
        char_offset_end=row[f"{row_prefix}_end"] or 0,
        bbox=bbox,
        confidence=float(row[f"{row_prefix}_conf"] or 1.0),
        is_failure_example=bool(row[f"{row_prefix}_fail"]),
        failure_notes=row[f"{row_prefix}_fail_notes"] or "",
        created_at=str(row[f"{row_prefix}_created"] or "")
    )

@router.get("", response_model=ShowcaseResponse)
def get_four_required_cases():
    """
    Dynamically queries SQLite database to assemble the four mandatory evaluation cases:
    1. A fact corroborated across documents (even if expressed differently).
    2. A genuine or likely contradiction.
    3. An apparent contradiction explained by context (time, scope, units).
    4. An extraction or reasoning failure and how it is mitigated.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cases = []

    query_template = """
        SELECT r.id as rel_id, r.relationship_type, r.confidence as rel_conf, r.reasoning as rel_reasoning,
               r.context_difference, r.case_category,
               f1.id as f1_id, f1.document_id as f1_doc_id, d1.filename as f1_doc_filename,
               f1.page_number as f1_page, f1.category as f1_category, f1.subject as f1_subject,
               f1.predicate as f1_predicate, f1.value as f1_value, f1.unit as f1_unit,
               f1.temporal_context as f1_temporal, f1.scope_context as f1_scope,
               f1.exact_quote as f1_quote, f1.char_offset_start as f1_start, f1.char_offset_end as f1_end,
               f1.bbox as f1_bbox, f1.confidence as f1_conf, f1.is_failure_example as f1_fail,
               f1.failure_notes as f1_fail_notes, f1.created_at as f1_created,
               f2.id as f2_id, f2.document_id as f2_doc_id, d2.filename as f2_doc_filename,
               f2.page_number as f2_page, f2.category as f2_category, f2.subject as f2_subject,
               f2.predicate as f2_predicate, f2.value as f2_value, f2.unit as f2_unit,
               f2.temporal_context as f2_temporal, f2.scope_context as f2_scope,
               f2.exact_quote as f2_quote, f2.char_offset_start as f2_start, f2.char_offset_end as f2_end,
               f2.bbox as f2_bbox, f2.confidence as f2_conf, f2.is_failure_example as f2_fail,
               f2.failure_notes as f2_fail_notes, f2.created_at as f2_created
        FROM relationships r
        JOIN facts f1 ON r.fact_id_1 = f1.id
        JOIN facts f2 ON r.fact_id_2 = f2.id
        JOIN documents d1 ON f1.document_id = d1.id
        JOIN documents d2 ON f2.document_id = d2.id
        WHERE r.relationship_type = ?
        ORDER BY r.confidence DESC, r.created_at DESC
        LIMIT 1
    """

    # 1. Case 1: Corroboration
    cursor.execute(query_template, ("corroboration",))
    row1 = cursor.fetchone()
    if row1:
        f1 = _row_to_fact_response("f1", row1)
        f2 = _row_to_fact_response("f2", row1)
        cases.append(ShowcaseCase(
            case_number=1,
            case_title=f"Cross-Document Fact Corroboration ({f1.subject})",
            case_type="corroboration",
            summary=f"Independent affirmation of {f1.subject} across {f1.document_filename} and {f2.document_filename}.",
            why_it_matters="Financial, macroeconomic, or operational metrics published across different reports originate from common underlying reality. The knowledge layer dynamically identifies equivalence despite differing formats or rounding.",
            fact_1=f1,
            fact_2=f2,
            reasoning=row1["rel_reasoning"],
            evidence_1={
                "document": f1.document_filename,
                "page": f1.page_number,
                "quote": f1.exact_quote,
                "char_range": [f1.char_offset_start, f1.char_offset_end],
                "bbox": f1.bbox
            },
            evidence_2={
                "document": f2.document_filename,
                "page": f2.page_number,
                "quote": f2.exact_quote,
                "char_range": [f2.char_offset_start, f2.char_offset_end],
                "bbox": f2.bbox
            }
        ))
    else:
        cases.append(ShowcaseCase(
            case_number=1,
            case_title="Cross-Document Fact Corroboration",
            case_type="corroboration",
            summary="Awaiting document ingestion to populate corroboration relationships dynamically.",
            why_it_matters="Detects independently confirmed facts across separate PDF documents.",
            reasoning="Upload documents with overlapping metrics to observe automatic corroboration."
        ))

    # 2. Case 2: Genuine Contradiction
    cursor.execute(query_template, ("genuine_contradiction",))
    row2 = cursor.fetchone()
    if row2:
        f1 = _row_to_fact_response("f1", row2)
        f2 = _row_to_fact_response("f2", row2)
        cases.append(ShowcaseCase(
            case_number=2,
            case_title=f"Genuine Contradiction ({f1.subject})",
            case_type="genuine_contradiction",
            summary=f"Direct empirical or institutional disagreement between {f1.document_filename} ({f1.value} {f1.unit}) and {f2.document_filename} ({f2.value} {f2.unit}).",
            why_it_matters="When different institutions or authors evaluate the same subject for the same period with incompatible outcomes, an epistemological system must highlight genuine conflict rather than forcing artificial consensus.",
            fact_1=f1,
            fact_2=f2,
            reasoning=row2["rel_reasoning"],
            evidence_1={
                "document": f1.document_filename,
                "page": f1.page_number,
                "quote": f1.exact_quote,
                "char_range": [f1.char_offset_start, f1.char_offset_end],
                "bbox": f1.bbox
            },
            evidence_2={
                "document": f2.document_filename,
                "page": f2.page_number,
                "quote": f2.exact_quote,
                "char_range": [f2.char_offset_start, f2.char_offset_end],
                "bbox": f2.bbox
            }
        ))
    else:
        cases.append(ShowcaseCase(
            case_number=2,
            case_title="Genuine Macroeconomic Contradiction",
            case_type="genuine_contradiction",
            summary="Awaiting document ingestion to identify empirical contradictions dynamically.",
            why_it_matters="Identifies conflicting assertions that cannot both be true under the same definition.",
            reasoning="Upload macroeconomic forecast reports (e.g. RBI vs IMF) to observe genuine disagreement detection."
        ))

    # 3. Case 3: Contextual Reconciliation
    cursor.execute(query_template, ("contextual_reconciliation",))
    row3 = cursor.fetchone()
    if row3:
        f1 = _row_to_fact_response("f1", row3)
        f2 = _row_to_fact_response("f2", row3)
        cases.append(ShowcaseCase(
            case_number=3,
            case_title=f"Apparent Contradiction Reconciled by Context ({f1.subject})",
            case_type="contextual_reconciliation",
            summary=f"Values differ ({f1.value} vs {f2.value}), but discrepancy is reconciled by {row3['context_difference'] or 'contextual differences'}.",
            why_it_matters="Most 'contradictions' in real-world PDF corpuses are not errors but differences in time horizon, scope (Consolidated vs Standalone), or legal versus colloquial terminology.",
            fact_1=f1,
            fact_2=f2,
            reasoning=row3["rel_reasoning"],
            evidence_1={
                "document": f1.document_filename,
                "page": f1.page_number,
                "quote": f1.exact_quote,
                "char_range": [f1.char_offset_start, f1.char_offset_end],
                "bbox": f1.bbox
            },
            evidence_2={
                "document": f2.document_filename,
                "page": f2.page_number,
                "quote": f2.exact_quote,
                "char_range": [f2.char_offset_start, f2.char_offset_end],
                "bbox": f2.bbox
            }
        ))
    else:
        cases.append(ShowcaseCase(
            case_number=3,
            case_title="Contextual Reconciliation",
            case_type="contextual_reconciliation",
            summary="Awaiting document ingestion to identify contextual reconciliations dynamically.",
            why_it_matters="Disambiguates apparent conflicts using temporal context, scope context, and unit conversions.",
            reasoning="Upload documents with different historical periods or reporting scopes to observe reconciliation."
        ))

    # 4. Case 4: Extraction Failure & Mitigation
    # Find fact flagged as failure example or relationship with extraction failure
    cursor.execute("""
        SELECT f.*, d.filename as document_filename
        FROM facts f
        JOIN documents d ON f.document_id = d.id
        WHERE f.is_failure_example = 1
        ORDER BY f.confidence ASC
        LIMIT 1
    """)
    row4 = cursor.fetchone()
    
    if row4:
        bbox_raw = row4["bbox"] if "bbox" in row4.keys() else "[]"
        try:
            bbox = json.loads(bbox_raw) if bbox_raw else []
        except Exception:
            bbox = []

        fail_fact = FactResponse(
            id=row4["id"],
            document_id=row4["document_id"],
            document_filename=row4["document_filename"],
            page_number=row4["page_number"],
            category=row4["category"],
            subject=row4["subject"],
            predicate=row4["predicate"],
            value=row4["value"],
            unit=row4["unit"] or "",
            temporal_context=row4["temporal_context"] or "",
            scope_context=row4["scope_context"] or "",
            exact_quote=row4["exact_quote"],
            char_offset_start=row4["char_offset_start"] or 0,
            char_offset_end=row4["char_offset_end"] or 0,
            bbox=bbox,
            confidence=float(row4["confidence"] or 0.7),
            is_failure_example=True,
            failure_notes=row4["failure_notes"] or "Multi-column layout ambiguity.",
            created_at=str(row4["created_at"])
        )

        cases.append(ShowcaseCase(
            case_number=4,
            case_title="Extraction Challenge & Layout Mitigation: Complex Multi-Column Layout",
            case_type="extraction_failure",
            summary="Dense multi-column tables and complex spanning headers create misalignment risks where plain text streams flatten columns into unintelligible sequences.",
            why_it_matters="Standard PDF scrapers that extract only continuous text streams transpose cell data from column B into column A, leading LLMs to hallucinate incorrect predicates or metrics.",
            fact_1=fail_fact,
            reasoning=fail_fact.failure_notes or "Multi-tier layout complexity required specialized table extraction to preserve hierarchical cell relationships.",
            evidence_1={
                "document": fail_fact.document_filename,
                "page": fail_fact.page_number,
                "quote": fail_fact.exact_quote,
                "char_range": [fail_fact.char_offset_start, fail_fact.char_offset_end],
                "bbox": fail_fact.bbox
            },
            resolution_or_mitigation="Engineered Mitigation: Integrated PyMuPDF's spatial table extraction (`page.find_tables()`) which detects cell grid coordinates and converts table structures into formatted Markdown tables with column headers explicitly bound before passing to the LLM prompt."
        ))
    else:
        # If no explicit failure flag in database, construct case highlighting the table mitigation architecture
        cases.append(ShowcaseCase(
            case_number=4,
            case_title="Extraction Challenge & Layout Mitigation: Table Structure Preservation",
            case_type="extraction_failure",
            summary="Dense multi-column tables with multi-tiered headers present parsing transposition risks in standard PDF text scrapers.",
            why_it_matters="Standard PDF parsers that extract only raw continuous text flatten columns into disordered lines, causing LLMs to misattribute numerical values to wrong headers.",
            reasoning="Unstructured text parsers fail to maintain column-to-header mapping in dense financial and macroeconomic tables without coordinate awareness.",
            resolution_or_mitigation="Engineered Mitigation: Integrated PyMuPDF's spatial table extraction (`page.find_tables()`) which detects cell grid coordinates and converts table structures into formatted Markdown tables with column headers explicitly bound before passing to the LLM prompt."
        ))

    conn.close()
    return ShowcaseResponse(cases=cases)
