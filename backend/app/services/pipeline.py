import os
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
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
    Coordinates PDF extraction, fact extraction, persistence, and reconciliation.
    """
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or shared_llm_client
        self.pdf_processor = PDFProcessor(max_pages=settings.MAX_PAGES_DEFAULT)
        self.fact_extractor = FactExtractor(self.llm)
        self.reconciler = FactReconciler(self.llm)

    def ingest_pdf(self, filepath: str | Path, dataset_tag: str = "uploaded", doc_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Ingests a PDF, extracts pages & text, extracts facts, persists to DB,
        and performs incremental reconciliation against all existing facts.
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        doc_id = doc_id or f"doc-{uuid.uuid4().hex[:8]}"
        filename = path.name

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # 1. Register document
            cursor.execute("""
                INSERT OR REPLACE INTO documents (id, filename, filepath, filesize, page_count, dataset_tag, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (doc_id, filename, str(path), path.stat().st_size, 0, dataset_tag, "processing"))
            conn.commit()

            # 2. Extract PDF layout and text
            logger.info(f"Extracting PDF: {filename}...")
            doc_data = self.pdf_processor.extract_document(path)
            
            cursor.execute("""
                UPDATE documents SET page_count = ?, filesize = ? WHERE id = ?
            """, (doc_data["total_pages"], doc_data["filesize"], doc_id))
            conn.commit()

            # 3. Store pages and extract facts
            all_new_facts = []
            for p in doc_data["pages"]:
                p_num = p["page_number"]
                p_text = p["text"]
                
                cursor.execute("""
                    INSERT OR REPLACE INTO document_pages (id, document_id, page_number, text_content, char_count, table_count)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (f"{doc_id}-p{p_num}", doc_id, p_num, p_text, p["char_count"], p["table_count"]))
                
                # Extract facts if page has substantive text
                if len(p_text.strip()) > 60:
                    page_facts = self.fact_extractor.extract_from_page(doc_id, p_num, p_text, filename)
                    all_new_facts.extend(page_facts)

            # 4. Save extracted facts into DB
            for f in all_new_facts:
                cursor.execute("""
                    INSERT OR REPLACE INTO facts (
                        id, document_id, page_number, category, subject, predicate, value, unit,
                        temporal_context, scope_context, exact_quote, char_offset_start, char_offset_end,
                        confidence, is_failure_example, failure_notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    f["id"], f["document_id"], f["page_number"], f["category"], f["subject"],
                    f["predicate"], f["value"], f.get("unit", ""), f.get("temporal_context", ""),
                    f.get("scope_context", ""), f["exact_quote"], f.get("char_offset_start", 0),
                    f.get("char_offset_end", 0), f.get("confidence", 1.0),
                    f.get("is_failure_example", 0), f.get("failure_notes", "")
                ))
            conn.commit()
            logger.info(f"Extracted {len(all_new_facts)} facts from {filename}")

            # 5. Incremental Reconciliation (Brownie point!)
            # Retrieve existing facts from OTHER documents
            cursor.execute("SELECT * FROM facts WHERE document_id != ?", (doc_id,))
            existing_rows = cursor.fetchall()
            existing_facts = [dict(r) for r in existing_rows]

            new_relationships = []
            if existing_facts and all_new_facts:
                logger.info(f"Reconciling {len(all_new_facts)} new facts against {len(existing_facts)} existing facts...")
                new_relationships = self.reconciler.reconcile_facts(existing_facts, all_new_facts)
                
                for rel in new_relationships:
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
                logger.info(f"Identified {len(new_relationships)} new cross-document relationships.")

            # 6. Mark document as ready
            summary = f"Processed {len(doc_data['pages'])} pages. Extracted {len(all_new_facts)} facts and established {len(new_relationships)} relationships."
            cursor.execute("UPDATE documents SET status = 'ready', summary = ? WHERE id = ?", (summary, doc_id))
            conn.commit()

            return {
                "document_id": doc_id,
                "filename": filename,
                "pages_processed": len(doc_data["pages"]),
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
