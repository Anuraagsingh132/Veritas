import re
import uuid
import logging
from typing import List, Dict, Any, Optional
from app.services.llm_client import LLMClient
from app.services.pdf_processor import PDFProcessor

logger = logging.getLogger(__name__)

FACT_EXTRACTION_SYSTEM_PROMPT = """You are an elite Knowledge Engineer and Fact Extraction Agent.
Your objective is to discover, extract, and ground meaningful NUMERICAL and SEMANTIC facts from the provided PDF page text.

Guidelines:
1. Dynamic Schema: Do NOT rely on pre-fixed fields. Let the document guide what constitutes a fact (financial metrics, macroeconomic projections, corporate dates, operational KPIs, policy targets, governance milestones).
2. Verbatim Grounding: EVERY fact MUST be backed by an exact, word-for-word quote from the text. Do not invent or summarize the quote.
3. Context Disambiguation: Explicitly extract:
   - temporal_context: Specific fiscal year, quarter, vintage date, or calendar period (e.g., 'FY24', 'FY 2023-24', 'June 22, 2011', 'Q4 FY24', 'FY26 Projections').
   - scope_context: Reporting scope, methodology, or accounting treatment (e.g., 'Consolidated', 'Standalone', 'Advance Estimate', 'Provisional', 'Staff Baseline', 'Pre-IPO').
   - unit: Exact monetary unit or metric dimension (e.g., 'INR Crores', 'INR Millions', 'Percent (%)', 'Sq. Ft.', 'PIN codes').
4. Detect Edge Cases / Extraction Pitfalls:
   If a fact comes from a complex table, footnote, or ambiguous wording where an extractor might misattribute numbers or miss units, flag it:
   - is_failure_example: true
   - failure_notes: Describe the extraction risk (e.g. 'Dense multi-column table where column headers could misalign').

Format your response as a JSON object:
{
  "facts": [
    {
      "category": "financial | operational | macroeconomic | corporate_governance | legal_entity | semantic",
      "subject": "Clear entity and metric name",
      "predicate": "Relationship or attribute (e.g., reported_revenue, projected_gdp_growth, founded_date)",
      "value": "Value as string",
      "unit": "Unit or scale (e.g. INR Crores, %, Pin Codes)",
      "temporal_context": "Exact time period or vintage",
      "scope_context": "Reporting scope or methodology",
      "exact_quote": "Exact verbatim sentence or table cell snippet from the text",
      "confidence": 0.95,
      "is_failure_example": false,
      "failure_notes": ""
    }
  ]
}
Extract up to 8 of the most critical and prominent facts from this text. Quality and grounding over quantity.
"""

class FactExtractor:
    """
    Extracts structured, grounded facts from PDF document text with dynamic schema inference.
    """
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def extract_from_page(self, doc_id: str, page_number: int, page_text: str, filename: str = "") -> List[Dict[str, Any]]:
        """
        Extracts facts from a single page's text using LLM or intelligent structural heuristics.
        """
        if not page_text or len(page_text.strip()) < 50:
            return []

        if self.llm.is_available():
            try:
                user_prompt = f"Document: {filename} (Page {page_number})\n\nContent:\n{page_text[:4000]}"
                response = self.llm.chat_json(FACT_EXTRACTION_SYSTEM_PROMPT, user_prompt)
                raw_facts = response.get("facts", [])
                
                processed_facts = []
                for f in raw_facts:
                    quote = f.get("exact_quote", "").strip()
                    start_off, end_off = PDFProcessor.locate_quote(page_text, quote)
                    
                    processed_facts.append({
                        "id": f"fact-{uuid.uuid4().hex[:10]}",
                        "document_id": doc_id,
                        "page_number": page_number,
                        "category": f.get("category", "semantic"),
                        "subject": f.get("subject", "Unspecified Subject"),
                        "predicate": f.get("predicate", "stated"),
                        "value": str(f.get("value", "")),
                        "unit": f.get("unit", ""),
                        "temporal_context": f.get("temporal_context", ""),
                        "scope_context": f.get("scope_context", ""),
                        "exact_quote": quote if quote else page_text[:200].strip(),
                        "char_offset_start": start_off,
                        "char_offset_end": end_off,
                        "confidence": float(f.get("confidence", 0.9)),
                        "is_failure_example": 1 if f.get("is_failure_example") else 0,
                        "failure_notes": f.get("failure_notes", "")
                    })
                return processed_facts
            except Exception as e:
                logger.warning(f"LLM fact extraction failed on page {page_number}: {e}. Falling back to structural extraction.")

        # Fallback: Structural regex & semantic heuristic extraction
        return self._heuristic_extract(doc_id, page_number, page_text, filename)

    def _heuristic_extract(self, doc_id: str, page_number: int, page_text: str, filename: str) -> List[Dict[str, Any]]:
        """
        High-precision pattern matcher for common financial, corporate, and macroeconomic facts
        when LLM is not actively queried or as fallback.
        """
        facts = []
        
        # 1. Revenue patterns (Crores, Millions, Billions)
        rev_matches = re.finditer(r'(?:revenue|income)\s*(?:from operations)?\s*(?:of|was|is|reached)?\s*(?:₹|Rs\.?|INR)?\s*([0-9,]+(?:\.[0-9]+)?)\s*(Cr(?:ore)?s?|Mn|Million|Billion)?', page_text, re.IGNORECASE)
        for m in rev_matches:
            val = m.group(1)
            unit = m.group(2) or "INR"
            # Look for surrounding sentence
            start = max(0, m.start() - 60)
            end = min(len(page_text), m.end() + 60)
            quote = page_text[start:end].strip()
            
            # Detect temporal context in snippet
            temp = "FY24" if "FY24" in quote or "2024" in quote else "Unspecified"
            
            facts.append({
                "id": f"fact-{uuid.uuid4().hex[:10]}",
                "document_id": doc_id,
                "page_number": page_number,
                "category": "financial",
                "subject": f"{filename.split('-')[1] if '-' in filename else 'Entity'} Revenue",
                "predicate": "revenue_from_operations",
                "value": val,
                "unit": unit,
                "temporal_context": temp,
                "scope_context": "Consolidated" if "consolidated" in quote.lower() else "General",
                "exact_quote": quote,
                "char_offset_start": m.start(),
                "char_offset_end": m.end(),
                "confidence": 0.85,
                "is_failure_example": 0,
                "failure_notes": ""
            })
            if len(facts) >= 2:
                break

        # 2. Growth / GDP rate patterns
        gdp_matches = re.finditer(r'(?:GDP|growth|expansion)\s*(?:rate|projection|estimate)?\s*(?:of|at|around)?\s*([0-9]+(?:\.[0-9]+)?)\s*%', page_text, re.IGNORECASE)
        for m in gdp_matches:
            val = m.group(1)
            start = max(0, m.start() - 50)
            end = min(len(page_text), m.end() + 50)
            quote = page_text[start:end].strip()
            temp = "FY26" if "FY26" in quote or "2025-26" in quote else ("FY25" if "FY25" in quote or "2024-25" in quote else "")
            
            facts.append({
                "id": f"fact-{uuid.uuid4().hex[:10]}",
                "document_id": doc_id,
                "page_number": page_number,
                "category": "macroeconomic",
                "subject": "Real GDP Growth",
                "predicate": "projected_growth_rate",
                "value": val,
                "unit": "%",
                "temporal_context": temp,
                "scope_context": "Staff Estimate" if "staff" in quote.lower() else "Official Projection",
                "exact_quote": quote,
                "char_offset_start": m.start(),
                "char_offset_end": m.end(),
                "confidence": 0.88,
                "is_failure_example": 0,
                "failure_notes": ""
            })
            if len(facts) >= 4:
                break

        # 3. Founding / Date / Corporate history patterns
        date_matches = re.finditer(r'(?:incorporated|founded|established|commenced operations)\s*(?:on|in)?\s*([A-Za-z]+\s+[0-9]{1,2},\s+[0-9]{4}|[A-Za-z]+\s+[0-9]{4}|[0-9]{4})', page_text, re.IGNORECASE)
        for m in date_matches:
            val = m.group(1)
            start = max(0, m.start() - 60)
            end = min(len(page_text), m.end() + 60)
            quote = page_text[start:end].strip()
            
            facts.append({
                "id": f"fact-{uuid.uuid4().hex[:10]}",
                "document_id": doc_id,
                "page_number": page_number,
                "category": "corporate_governance",
                "subject": "Corporate Inception",
                "predicate": "founding_or_incorporation_date",
                "value": val,
                "unit": "Date",
                "temporal_context": val,
                "scope_context": "Legal Entity History",
                "exact_quote": quote,
                "char_offset_start": m.start(),
                "char_offset_end": m.end(),
                "confidence": 0.92,
                "is_failure_example": 0,
                "failure_notes": ""
            })
            if len(facts) >= 5:
                break

        return facts
