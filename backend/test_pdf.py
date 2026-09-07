import sys
from pathlib import Path
from app.services.pdf_processor import PDFProcessor

def test_pdf_extraction():
    pdf_path = Path("starter-datasets/delhivery/03-delhivery-q4-fy24-earnings-presentation.pdf")
    if not pdf_path.exists():
        pdf_path = Path("../starter-datasets/delhivery/03-delhivery-q4-fy24-earnings-presentation.pdf")
    
    print(f"Testing extraction on: {pdf_path.resolve()}")
    processor = PDFProcessor(max_pages=5)
    doc_data = processor.extract_document(pdf_path)
    
    print(f"[OK] Extracted {doc_data['processed_pages']} pages of {doc_data['total_pages']} total pages.")
    print(f"[OK] Total characters extracted: {doc_data['total_chars']}")
    print(f"[OK] Total tables detected: {doc_data['total_tables']}")
    
    # Check page 4 text
    if len(doc_data["pages"]) >= 4:
        p4 = doc_data["pages"][3]
        print(f"[OK] Sample text from page {p4['page_number']} (first 250 chars):\n{p4['text'][:250].strip()}")

if __name__ == "__main__":
    test_pdf_extraction()
