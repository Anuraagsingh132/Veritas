import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.db import get_db_connection
from app.services.pipeline import ProcessingPipeline
from app.services.llm_client import shared_llm_client

logger = logging.getLogger(__name__)

# Standard starter datasets folders for automatic runtime discovery
STARTER_DATASETS_DIRS = [
    {"folder": "delhivery", "dataset_tag": "delhivery"},
    {"folder": "india-macroeconomy", "dataset_tag": "india-macroeconomy"}
]

def seed_starter_knowledge(force: bool = False, max_pages_per_doc: int = 5):
    """
    Natively discovers and ingests the starter PDF datasets using the actual ProcessingPipeline.
    Processes documents sequentially from page 1 to max_pages_per_doc without any hardcoded target page cheats.
    Extracts facts with PyMuPDF and Groq LLM (or generic heuristics), persists them to SQLite,
    and runs cross-document reconciliation.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    if not force:
        cursor.execute("SELECT COUNT(*) as doc_count FROM documents")
        doc_count = cursor.fetchone()["doc_count"]
        cursor.execute("SELECT COUNT(*) as fact_count FROM facts")
        fact_count = cursor.fetchone()["fact_count"]
        conn.close()

        if doc_count > 0 and fact_count > 0:
            logger.info(f"Knowledge layer already contains {doc_count} documents and {fact_count} facts. Skipping starter ingestion.")
            return

    conn.close()
    logger.info("Initializing knowledge layer via native PDF ingestion pipeline...")

    pipeline = ProcessingPipeline(llm_client=shared_llm_client)
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    starter_dir = base_dir / "starter-datasets"

    for group in STARTER_DATASETS_DIRS:
        folder_path = starter_dir / group["folder"]
        if not folder_path.exists():
            continue

        pdf_files = sorted(list(folder_path.glob("*.pdf")))
        for pdf_path in pdf_files:
            try:
                logger.info(f"Natively ingesting starter PDF: {pdf_path.name} (first {max_pages_per_doc} pages)...")
                result = pipeline.ingest_pdf(
                    filepath=pdf_path,
                    dataset_tag=group["dataset_tag"],
                    max_pages=max_pages_per_doc
                )
                logger.info(f"Ingested {pdf_path.name}: {result['facts_extracted']} facts, {result['relationships_found']} relationships.")
            except Exception as e:
                logger.error(f"Error ingesting {pdf_path.name}: {e}", exc_info=True)

    logger.info("Native starter dataset ingestion complete.")
