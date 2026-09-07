import uuid
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from app.config import settings
from app.db import get_db_connection
from app.services.pdf_processor import PDFProcessor
from app.services.fact_extractor import FactExtractor
from app.services.reconciler import FactReconciler
from app.services.llm_client import LLMClient, shared_llm_client

logger = logging.getLogger(__name__)

class ProcessingPipeline:
    """
    End-to-end ingestion and knowledge graph construction pipeline.
    Coordinates PDF layout extraction, table structuring, fact extraction,
    persistence, and incremental cross-document reconciliation.
    """
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or shared_llm_client
        self.pdf_processor = PDFProcessor(max_pages=settings.MAX_PAGES_DEFAULT)
        self.fact_extractor = FactExtractor(self.llm)
        self.reconciler = FactReconciler(self.llm)

    def ingest_pdf(
        self,
        filepath: str | Path,
        dataset_tag: str = "uploaded",
        doc_id: Optional[str] = None,
        max_pages: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Ingests a PDF, extracts layout & tables, extracts facts via LLM or heuristics,
        persists to SQLite, and incrementally reconciles new facts against the knowledge layer.
        """
        path = Path(filepath)
        filename = path.name
        doc_id = doc_id or f"doc-{uuid.uuid4().hex[:8]}"

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # 1. Register document record with initial progress
            cursor.execute("""
                INSERT OR REPLACE INTO documents (
                    id, filename, filepath, filesize, page_count, dataset_tag, 
                    status, summary, processed_pages, total_pages, current_step, progress_pct
                ) VALUES (?, ?, ?, ?, ?, ?, 'processing', 'Analyzing PDF layout and detecting tables...', 0, 0, 'Parsing layout & tables', 5)
            """, (doc_id, filename, str(path), path.stat().st_size if path.exists() else 0, 0, dataset_tag))
            conn.commit()

            # 2. Extract layout, text, tables, and bounding boxes
            logger.info(f"Extracting PDF: {filename}...")
            if max_pages:
                custom_processor = PDFProcessor(max_pages=max_pages)
                doc_data = custom_processor.extract_document(path)
            else:
                doc_data = self.pdf_processor.extract_document(path)
            
            pages_to_process = doc_data["pages"]
            total_target = len(pages_to_process)
            
            cursor.execute("""
                UPDATE documents 
                SET page_count = ?, filesize = ?, total_pages = ?, processed_pages = 0,
                    progress_pct = 10, current_step = 'Starting fact extraction',
                    summary = ?
                WHERE id = ?
            """, (doc_data["total_pages"], doc_data["filesize"], total_target, f"Extracted {total_target} pages. Beginning fact discovery...", doc_id))
            conn.commit()

            # 3. Store pages and extract facts with live progress updates
            all_new_facts = []
            for idx, p in enumerate(pages_to_process, 1):
                p_num = p["page_number"]
                p_text = p["text"]
                
                cursor.execute("""
                    INSERT OR REPLACE INTO document_pages (id, document_id, page_number, text_content, char_count, table_count)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (f"{doc_id}-p{p_num}", doc_id, p_num, p_text, p["char_count"], p["table_count"]))
                
                # Extract facts if page has substantive text or tables
                if len(p_text.strip()) > 50 or p["tables"]:
                    page_facts = self.fact_extractor.extract_from_page(
                        doc_id=doc_id,
                        page_number=p_num,
                        page_text=p_text,
                        tables=p["tables"],
                        blocks=p["blocks"],
                        filename=filename
                    )
                    all_new_facts.extend(page_facts)

                # Update live progress after each page
                pct = int(10 + (idx / total_target) * 70)
                cursor.execute("""
                    UPDATE documents 
                    SET processed_pages = ?, 
                        progress_pct = ?, 
                        current_step = ?, 
                        summary = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    idx, 
                    pct, 
                    f"Processing page {idx} of {total_target}",
                    f"Processing page {idx}/{total_target} ({len(all_new_facts)} facts discovered so far)...",
                    doc_id
                ))
                conn.commit()

            # 4. Save extracted facts into DB with bounding box visual grounding
            for f in all_new_facts:
                bbox_json = json.dumps(f.get("bbox", []))
                cursor.execute("""
                    INSERT OR REPLACE INTO facts (
                        id, document_id, page_number, category, subject, predicate, value, unit,
                        temporal_context, scope_context, exact_quote, char_offset_start, char_offset_end,
                        confidence, is_failure_example, failure_notes, bbox
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    f["id"], f["document_id"], f["page_number"], f["category"], f["subject"],
                    f["predicate"], f["value"], f.get("unit", ""), f.get("temporal_context", ""),
                    f.get("scope_context", ""), f["exact_quote"], f.get("char_offset_start", 0),
                    f.get("char_offset_end", 0), f.get("confidence", 1.0),
                    f.get("is_failure_example", 0), f.get("failure_notes", ""), bbox_json
                ))
            conn.commit()
            logger.info(f"Extracted {len(all_new_facts)} facts from {filename}")

            # 5. Incremental Reconciliation (Brownie point!)
            # Retrieve existing facts from OTHER documents that are verified and ready
            cursor.execute("""
                SELECT f.* FROM facts f
                INNER JOIN documents d ON f.document_id = d.id
                WHERE f.document_id != ? AND d.status = 'ready'
            """, (doc_id,))
            existing_rows = cursor.fetchall()
            existing_facts = [dict(r) for r in existing_rows]

            new_relationships = []
            if existing_facts and all_new_facts:
                cursor.execute("""
                    UPDATE documents 
                    SET progress_pct = 85, 
                        current_step = 'Reconciling cross-document knowledge',
                        summary = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (f"Discovered {len(all_new_facts)} facts. Reconciling against existing knowledge layer...", doc_id))
                conn.commit()

                logger.info(f"Reconciling {len(all_new_facts)} new facts against {len(existing_facts)} existing facts...")
                new_relationships = self.reconciler.reconcile_facts(existing_facts, all_new_facts)
                
                for rel in new_relationships:
                    try:
                        cursor.execute("""
                            INSERT OR REPLACE INTO relationships (
                                id, fact_id_1, fact_id_2, doc_id_1, doc_id_2, relationship_type,
                                confidence, reasoning, context_difference, case_category
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            rel["id"], rel["fact_id_1"], rel["fact_id_2"], rel["doc_id_1"], rel["doc_id_2"],
                            rel["relationship_type"], rel.get("confidence", 1.0), rel["reasoning"],
                            rel.get("context_difference", ""), rel.get("case_category", "")
                        ))
                    except Exception as rel_err:
                        logger.warning(f"Skipping relationship insert for {rel.get('id')}: {rel_err}")
                conn.commit()
                logger.info(f"Identified {len(new_relationships)} new cross-document relationships.")

            # 6. Mark document as ready
            summary = f"Processed {total_target} pages. Extracted {len(all_new_facts)} facts and established {len(new_relationships)} cross-document relationships."
            cursor.execute("""
                UPDATE documents 
                SET status = 'ready', 
                    processed_pages = ?, 
                    total_pages = ?,
                    progress_pct = 100, 
                    current_step = 'Completed',
                    summary = ?, 
                    updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, (total_target, total_target, summary, doc_id))
            conn.commit()

            return {
                "document_id": doc_id,
                "filename": filename,
                "pages_processed": total_target,
                "facts_extracted": len(all_new_facts),
                "relationships_found": len(new_relationships)
            }

        except Exception as e:
            logger.error(f"Ingestion failed for {filename}: {e}", exc_info=True)
            cursor.execute("UPDATE documents SET status = 'error', summary = ? WHERE id = ?", (str(e), doc_id))
            conn.commit()
            raise e
        finally:
            conn.close()

    def reconcile_all_existing(self) -> int:
        """
        Runs complete pairwise reconciliation across all facts currently in the database.
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM facts")
        facts = [dict(r) for r in cursor.fetchall()]
        
        if not facts:
            conn.close()
            return 0

        relationships = self.reconciler.reconcile_facts(facts)
        
        for rel in relationships:
            cursor.execute("""
                INSERT OR REPLACE INTO relationships (
                    id, fact_id_1, fact_id_2, doc_id_1, doc_id_2, relationship_type,
                    confidence, reasoning, context_difference, case_category
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                rel["id"], rel["fact_id_1"], rel["fact_id_2"], rel["doc_id_1"], rel["doc_id_2"],
                rel["relationship_type"], rel.get("confidence", 1.0), rel["reasoning"],
                rel.get("context_difference", ""), rel.get("case_category", "")
            ))
            
        conn.commit()
        conn.close()
        return len(relationships)
