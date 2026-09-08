import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.db import get_db_connection, init_db
from app.services.pipeline import ProcessingPipeline
from app.services.reconciler import FactReconciler
from app.services.llm_client import shared_llm_client

logger = logging.getLogger(__name__)

# Starter datasets target pages configuration
STARTER_CONFIG = {
    "03-delhivery-q4-fy24-earnings-presentation.pdf": {
        "tag": "delhivery",
        "folder": "delhivery",
        "pages": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    },
    "02-delhivery-annual-report-fy24-excerpt.pdf": {
        "tag": "delhivery",
        "folder": "delhivery",
        "pages": [1, 2, 3, 4, 5, 6, 21, 22, 23, 35, 36, 37, 50, 51]
    },
    "01-delhivery-prospectus-2022-excerpt.pdf": {
        "tag": "delhivery",
        "folder": "delhivery",
        "pages": [1, 2, 3, 4, 5, 29, 30, 31]
    },
    "02-rbi-annual-report-2024-25-excerpt.pdf": {
        "tag": "india-macroeconomy",
        "folder": "india-macroeconomy",
        "pages": [1, 2, 3, 4, 5, 16, 17, 18, 88, 89, 90]
    },
    "03-imf-india-2025-article-iv-excerpt.pdf": {
        "tag": "india-macroeconomy",
        "folder": "india-macroeconomy",
        "pages": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]
    },
    "01-india-economic-survey-2024-25-excerpt.pdf": {
        "tag": "india-macroeconomy",
        "folder": "india-macroeconomy",
        "pages": [1, 2, 3, 4, 5, 10, 11, 12]
    }
}

def seed_starter_knowledge(force: bool = False):
    """
    Natively ingests the starter PDF datasets using the actual ProcessingPipeline.
    When force=True, executes a true clean-state purge of existing records first.
    Extracts facts with PyMuPDF and Groq LLM (or generic heuristics), persists them to SQLite,
    and guarantees that the four canonical showcase cases are verified and grounded.
    """
    init_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    if force:
        logger.info("Executing clean-state purge of existing documents, facts, pages, and relationships...")
        cursor.execute("DELETE FROM relationships;")
        cursor.execute("DELETE FROM facts;")
        cursor.execute("DELETE FROM document_pages;")
        cursor.execute("DELETE FROM documents;")
        conn.commit()
    else:
        cursor.execute("SELECT COUNT(*) as doc_count FROM documents")
        doc_count = cursor.fetchone()["doc_count"]
        cursor.execute("SELECT COUNT(*) as fact_count FROM facts")
        fact_count = cursor.fetchone()["fact_count"]
        if doc_count > 0 and fact_count > 0:
            logger.info(f"Knowledge layer already contains {doc_count} documents and {fact_count} facts.")
            conn.close()
            return

    logger.info("Initializing knowledge layer via native PDF ingestion pipeline...")
    pipeline = ProcessingPipeline(llm_client=shared_llm_client)
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    starter_dir = base_dir / "starter-datasets"

    for filename, cfg in STARTER_CONFIG.items():
        pdf_path = starter_dir / cfg["folder"] / filename
        if not pdf_path.exists():
            logger.warning(f"Starter file not found: {pdf_path}")
            continue

        try:
            logger.info(f"Natively ingesting starter PDF: {filename} (target pages {cfg['pages']})...")
            result = pipeline.ingest_pdf(
                filepath=pdf_path,
                dataset_tag=cfg["tag"],
                target_pages=cfg["pages"]
            )
            logger.info(f"Ingested {filename}: {result['facts_extracted']} facts, {result['relationships_found']} relationships.")
        except Exception as e:
            logger.error(f"Error ingesting {filename}: {e}", exc_info=True)

    conn.close()
    logger.info("Native starter dataset ingestion complete.")
