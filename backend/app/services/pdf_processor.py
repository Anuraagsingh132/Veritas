import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import pymupdf  # Modern PyMuPDF API

logger = logging.getLogger(__name__)

class PDFProcessor:
    """
    Robust PDF extractor handling layout, tables, page offsets, and large documents.
    Preserves exact character offsets and page numbering for evidence grounding.
    """
    
    def __init__(self, max_pages: int = 100):
        self.max_pages = max_pages

    def extract_document(self, filepath: str | Path) -> Dict[str, Any]:
        """
        Extracts metadata and full page-by-page text content with layout cues.
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"PDF file not found: {path}")

        doc = pymupdf.open(str(path))
        total_pages = len(doc)
        pages_to_process = min(total_pages, self.max_pages)
        
        metadata = doc.metadata or {}
        extracted_pages = []
        
        total_chars = 0
        total_tables = 0

        for page_idx in range(pages_to_process):
            page_num = page_idx + 1
            page = doc[page_idx]
            
            # Extract plain text with layout preserved
            text = page.get_text("text") or ""
            
            # Detect tables if available
            tables = []
            try:
                tabs = page.find_tables()
                if tabs and tabs.tables:
                    for tab in tabs.tables:
                        df_or_rows = tab.extract()
                        if df_or_rows:
                            tables.append(df_or_rows)
            except Exception as e:
                logger.debug(f"Table detection skipped on page {page_num}: {e}")
            
            # Extract text blocks with bbox for spatial grounding
            blocks = []
            try:
                raw_blocks = page.get_text("blocks")
                for b in raw_blocks:
                    # b format: (x0, y0, x1, y1, text, block_no, block_type)
                    if len(b) >= 5 and b[4].strip():
                        blocks.append({
                            "bbox": [round(b[0], 2), round(b[1], 2), round(b[2], 2), round(b[3], 2)],
                            "text": b[4].strip()
                        })
            except Exception as e:
                logger.debug(f"Block extraction skipped on page {page_num}: {e}")
            
            page_char_count = len(text)
            total_chars += page_char_count
            total_tables += len(tables)

            extracted_pages.append({
                "page_number": page_num,
                "text": text,
                "char_count": page_char_count,
                "table_count": len(tables),
                "tables": tables,
                "blocks": blocks
            })

        doc.close()
        
        return {
            "filename": path.name,
            "filepath": str(path),
            "filesize": path.stat().st_size,
            "total_pages": total_pages,
            "processed_pages": pages_to_process,
            "metadata": metadata,
            "total_chars": total_chars,
            "total_tables": total_tables,
            "pages": extracted_pages
        }

    @staticmethod
    def locate_quote(page_text: str, quote: str) -> tuple[int, int]:
        """
        Finds start and end offsets of an exact or normalized quote inside a page.
        """
        if not quote or not page_text:
            return 0, 0
        
        # Direct match
        idx = page_text.find(quote)
        if idx != -1:
            return idx, idx + len(quote)
            
        # Whitespace-collapsed match
        norm_page = " ".join(page_text.split())
        norm_quote = " ".join(quote.split())
        idx = norm_page.find(norm_quote)
        if idx != -1:
            return idx, idx + len(norm_quote)

        # Truncated substring match
        sub = quote[:min(len(quote), 50)]
        idx = page_text.find(sub)
        if idx != -1:
            return idx, idx + len(quote)
            
        return 0, len(quote)
