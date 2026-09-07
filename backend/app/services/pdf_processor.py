import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pymupdf  # Modern PyMuPDF API

logger = logging.getLogger(__name__)

class PDFProcessor:
    """
    Robust PDF extractor handling layout, tables, page offsets, and large documents.
    Preserves exact character offsets, spatial bounding boxes, and table structures.
    """
    
    def __init__(self, max_pages: int = 100):
        self.max_pages = max_pages

    def extract_document(self, filepath: str | Path) -> Dict[str, Any]:
        """
        Extracts metadata and full page-by-page text content with layout cues,
        table extraction, and spatial bounding boxes.
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
            
            # Detect and extract structured tables
            tables = []
            try:
                tabs = page.find_tables()
                if tabs and tabs.tables:
                    for tab in tabs.tables:
                        df_or_rows = tab.extract()
                        if df_or_rows:
                            # Filter empty rows
                            cleaned_rows = [
                                [str(cell).strip() if cell is not None else "" for cell in row]
                                for row in df_or_rows if any(cell for cell in row)
                            ]
                            if cleaned_rows:
                                tables.append({
                                    "bbox": list(tab.bbox),
                                    "rows": cleaned_rows,
                                    "row_count": len(cleaned_rows),
                                    "col_count": len(cleaned_rows[0]) if cleaned_rows else 0
                                })
            except Exception as e:
                logger.debug(f"Table detection skipped on page {page_num}: {e}")
            
            # Extract text blocks with bbox for spatial visual grounding
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
    def format_tables_as_markdown(tables: List[Dict[str, Any]]) -> str:
        """
        Converts extracted table structures into clean Markdown tables so the LLM
        can easily parse multi-column financial and macroeconomic data.
        """
        if not tables:
            return ""

        md_parts = []
        for idx, tbl in enumerate(tables, 1):
            rows = tbl.get("rows", [])
            if not rows:
                continue
            
            md_parts.append(f"\n[Table {idx} (Coordinates: {tbl.get('bbox', [])})]")
            # Header
            header = rows[0]
            md_parts.append("| " + " | ".join(header) + " |")
            md_parts.append("| " + " | ".join(["---"] * len(header)) + " |")
            # Data rows
            for row in rows[1:]:
                # Pad or truncate row to match header length
                padded = row[:len(header)] + [""] * max(0, len(header) - len(row))
                md_parts.append("| " + " | ".join(padded) + " |")

        return "\n".join(md_parts)

    @staticmethod
    def locate_quote(page_text: str, quote: str) -> Tuple[int, int]:
        """
        Finds start and end character offsets of a quote inside page text.
        """
        start, end, _ = PDFProcessor.locate_quote_with_bbox(page_text, [], quote)
        return start, end

    @staticmethod
    def locate_quote_with_bbox(
        page_text: str,
        blocks: List[Dict[str, Any]],
        quote: str
    ) -> Tuple[int, int, List[float]]:
        """
        Finds character offsets AND spatial bounding box [x0, y0, x1, y1]
        for a verbatim or normalized quote.
        """
        if not quote or not page_text:
            return 0, 0, []

        clean_quote = quote.strip()
        start_idx = -1
        end_idx = -1

        # 1. Direct match
        idx = page_text.find(clean_quote)
        if idx != -1:
            start_idx = idx
            end_idx = idx + len(clean_quote)
        else:
            # 2. Normalized whitespace & currency symbol match (e.g. ₹ vs Rs)
            norm_page = re.sub(r'\s+', ' ', page_text)
            norm_quote = re.sub(r'\s+', ' ', clean_quote)
            norm_page_sub = norm_page.replace('Rs.', '₹').replace('Rs', '₹')
            norm_quote_sub = norm_quote.replace('Rs.', '₹').replace('Rs', '₹')
            
            idx = norm_page_sub.find(norm_quote_sub)
            if idx != -1:
                start_idx = idx
                end_idx = idx + len(norm_quote)
            else:
                # 3. Substring match (first 40 characters)
                sub = clean_quote[:min(len(clean_quote), 40)]
                idx = page_text.lower().find(sub.lower())
                if idx != -1:
                    start_idx = idx
                    end_idx = min(len(page_text), idx + len(clean_quote))
                else:
                    start_idx = 0
                    end_idx = min(len(page_text), len(clean_quote))

        # 4. Find matching spatial bounding box from text blocks
        bbox = []
        if blocks:
            # Look for block containing the quote snippet
            search_token = clean_quote[:min(len(clean_quote), 30)].lower()
            for b in blocks:
                b_text = b.get("text", "").lower()
                if search_token and search_token in b_text:
                    bbox = b.get("bbox", [])
                    break
            
            # Fallback: if not found, search for any prominent number in the quote
            if not bbox:
                numbers = re.findall(r'\b\d+(?:,\d+)*(?:\.\d+)?\b', clean_quote)
                if numbers:
                    target_num = numbers[0]
                    for b in blocks:
                        if target_num in b.get("text", ""):
                            bbox = b.get("bbox", [])
                            break

        return start_idx, end_idx, bbox
