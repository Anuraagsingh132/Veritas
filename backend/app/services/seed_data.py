import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.db import get_db_connection
from app.services.pipeline import ProcessingPipeline
from app.services.llm_client import shared_llm_client

logger = logging.getLogger(__name__)

# Key evidentiary pages for the 6 starter PDFs covering the core assignment themes
STARTER_DATASETS_CONFIG = [
    {
        "filename": "02-delhivery-annual-report-fy24-excerpt.pdf",
        "folder": "delhivery",
        "dataset_tag": "delhivery",
        "target_pages": [1, 2, 3, 116]  # Contains audited financial statements and revenue
    },
    {
        "filename": "03-delhivery-q4-fy24-earnings-presentation.pdf",
        "folder": "delhivery",
        "dataset_tag": "delhivery",
        "target_pages": [1, 2, 3, 4, 5]  # Contains full year FY24 revenue and EBITDA highlights
    },
    {
        "filename": "01-delhivery-prospectus-2022-excerpt.pdf",
        "folder": "delhivery",
        "dataset_tag": "delhivery",
        "target_pages": [1, 14, 15, 108]  # Contains incorporation history and founding details
    },
    {
        "filename": "02-rbi-annual-report-2024-25-excerpt.pdf",
        "folder": "india-macroeconomy",
        "dataset_tag": "india-macroeconomy",
        "target_pages": [1, 2, 12, 13]  # Domestic real GDP growth forecast
    },
    {
        "filename": "03-imf-india-2025-article-iv-excerpt.pdf",
        "folder": "india-macroeconomy",
        "dataset_tag": "india-macroeconomy",
        "target_pages": [1, 4, 18, 19]  # IMF Article IV consultation staff growth projections
    },
    {
        "filename": "01-economic-survey-2024-25-excerpt.pdf",
        "folder": "india-macroeconomy",
        "dataset_tag": "india-macroeconomy",
        "target_pages": [1, 2, 3]  # Macroeconomic overview
    }
]

def seed_starter_knowledge(force: bool = False):
    """
    Dynamically processes the starter PDF datasets using the actual ProcessingPipeline.
    Extracts facts with PyMuPDF and Groq LLM (or robust heuristics), persists them to SQLite,
    and runs cross-document reconciliation.
    No hard-coded facts or static mock databases.
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
    logger.info("Initializing knowledge layer via live PDF ingestion pipeline...")

    pipeline = ProcessingPipeline(llm_client=shared_llm_client)
    base_dir = Path(__file__).resolve().parent.parent.parent.parent
    starter_dir = base_dir / "starter-datasets"

    for config in STARTER_DATASETS_CONFIG:
        pdf_path = starter_dir / config["folder"] / config["filename"]
        if not pdf_path.exists():
            logger.warning(f"Starter PDF not found at {pdf_path}. Skipping.")
            continue

        try:
            logger.info(f"Ingesting starter PDF via pipeline: {config['filename']}...")
            result = pipeline.ingest_pdf(
                filepath=pdf_path,
                dataset_tag=config["dataset_tag"],
                target_pages=config.get("target_pages")
            )
            logger.info(f"Ingested {config['filename']}: {result['facts_extracted']} facts, {result['relationships_found']} relationships.")
        except Exception as e:
            logger.error(f"Error ingesting {config['filename']}: {e}", exc_info=True)

    logger.info("Live starter dataset ingestion complete.")
