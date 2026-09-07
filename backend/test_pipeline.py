import sys
from pathlib import Path
from app.services.pipeline import ProcessingPipeline
from app.db import get_db_connection

def test_pipeline_ingest():
    pdf_path = Path("starter-datasets/delhivery/03-delhivery-q4-fy24-earnings-presentation.pdf")
    if not pdf_path.exists():
        pdf_path = Path("../starter-datasets/delhivery/03-delhivery-q4-fy24-earnings-presentation.pdf")
        
    pipeline = ProcessingPipeline()
    print("Ingesting PDF into pipeline...")
    result = pipeline.ingest_pdf(pdf_path, dataset_tag="live-test", doc_id="test-doc-delhivery-q4")
    print(f"[OK] Pipeline ingestion result: {result}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM facts WHERE document_id = 'test-doc-delhivery-q4'")
    fact_count = cursor.fetchone()[0]
    print(f"[OK] Total facts stored for test document: {fact_count}")
    conn.close()

if __name__ == "__main__":
    test_pipeline_ingest()
