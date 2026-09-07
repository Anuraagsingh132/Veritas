import sys
import json
from pathlib import Path
from app.services.pipeline import ProcessingPipeline
from app.db import get_db_connection

def test_pipeline_ingest():
    pdf_path = Path("starter-datasets/delhivery/03-delhivery-q4-fy24-earnings-presentation.pdf")
    if not pdf_path.exists():
        pdf_path = Path("../starter-datasets/delhivery/03-delhivery-q4-fy24-earnings-presentation.pdf")
        
    pipeline = ProcessingPipeline()
    print("Ingesting PDF into pipeline with layout and table analysis...")
    result = pipeline.ingest_pdf(
        filepath=pdf_path,
        dataset_tag="live-test",
        doc_id="test-doc-delhivery-q4",
        target_pages=[1, 2, 3, 4, 5]
    )
    print(f"[OK] Pipeline ingestion result: {result}")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, subject, value, unit, exact_quote, bbox FROM facts WHERE document_id = 'test-doc-delhivery-q4'")
    facts = cursor.fetchall()
    print(f"[OK] Total facts stored for test document: {len(facts)}")
    assert len(facts) > 0, "Pipeline failed to extract facts from test document"
    
    for f in facts[:3]:
        safe_subject = str(f["subject"]).encode('ascii', 'replace').decode('ascii')
        print(f"     * Fact: {safe_subject} = {f['value']} {f['unit']}")
        print(f"       Quote: \"{f['exact_quote'][:60].encode('ascii', 'replace').decode('ascii')}...\"")
        print(f"       Bbox: {f['bbox']}")

    conn.close()
    print("[OK] Pipeline end-to-end test PASSED successfully!")

if __name__ == "__main__":
    test_pipeline_ingest()
