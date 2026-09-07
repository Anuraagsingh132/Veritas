import re
import uuid
import json
import logging
from typing import List, Dict, Any, Optional
from app.services.llm_client import LLMClient
from app.services.pdf_processor import PDFProcessor

logger = logging.getLogger(__name__)

FACT_EXTRACTION_SYSTEM_PROMPT = """You are an elite Knowledge Engineer and Fact Extraction Agent.
Your objective is to discover, extract, and ground meaningful NUMERICAL and SEMANTIC facts from the provided PDF page content and any detected tables.

Guidelines:
1. Dynamic Schema: Let the document guide what constitutes a fact. Do NOT force a fixed schema. Extract quantitative assertions, financial indicators, operational metrics, scientific findings, dates, entity milestones, and key predicates.
2. Verbatim Grounding: EVERY fact MUST be backed by an exact, word-for-word quote from the text or table cell. Do not paraphrase or synthesize the quote.
3. Context Disambiguation: Explicitly extract:
   - temporal_context: Specific fiscal year, quarter, calendar date, or vintage period if mentioned (e.g. 'FY 2023-24', 'May 2011', 'Q4 FY24', '2025-26', 'Staff Baseline Projection').
   - scope_context: Reporting scope, methodology, or accounting treatment (e.g. 'Consolidated', 'Standalone', 'Advance Estimate', 'Provisional', 'Staff Baseline', 'Pre-IPO').
   - unit: Exact unit or scale (e.g. 'INR Crores', 'Percent (%)', 'km/h', 'PIN Codes', 'Units', 'Million USD').
4. Multi-Column Tables & Layout Risk (Case 4 Handling):
   If a fact is extracted from a complex table, footnote, or dense multi-column layout where column headers could misalign or be transposed, flag it:
   - is_failure_example: true
   - failure_notes: "Dense multi-column table layout where multi-tiered column headers require coordinate cell bounding to avoid transposition."
   Otherwise:
   - is_failure_example: false
   - failure_notes: ""

Format your response as a JSON object:
{
  "facts": [
    {
      "category": "financial | operational | macroeconomic | corporate_governance | scientific | semantic",
      "subject": "Clear entity and metric name (e.g. Delhivery Limited Consolidated Revenue from Operations)",
      "predicate": "Attribute or relationship (e.g. reported_annual_revenue, projected_real_gdp_growth)",
      "value": "Normalized numerical or semantic value as string",
      "unit": "Unit of measurement or scale if applicable",
      "temporal_context": "Exact time period or vintage",
      "scope_context": "Reporting scope or methodology",
      "exact_quote": "Verbatim sentence or table row excerpt backing this fact",
      "confidence": 0.95,
      "is_failure_example": false,
      "failure_notes": ""
    }
  ]
}
Extract up to 8 of the most critical and prominent facts from this page. Focus on high precision and verbatim evidence grounding.
"""

class FactExtractor:
    """
    Extracts structured, grounded facts from PDF document text with dynamic schema inference,
    table structure preservation, and spatial visual coordinates.
    """
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def extract_from_page(
        self,
        doc_id: str,
        page_number: int,
        page_text: str,
        tables: Optional[List[Dict[str, Any]]] = None,
        blocks: Optional[List[Dict[str, Any]]] = None,
        filename: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Extracts facts from a single page's text and structured tables using LLM or
        domain-agnostic structural heuristics.
        """
        if not page_text or len(page_text.strip()) < 40:
            return []

        tables = tables or []
        blocks = blocks or []

        # 1. Try LLM Extraction if available
        if self.llm.is_available():
            try:
                table_md = PDFProcessor.format_tables_as_markdown(tables)
                
                user_prompt = f"Document: {filename} (Page {page_number})\n\n"
                if table_md:
                    user_prompt += f"[Detected Tables on Page (Structure Preserved)]:\n{table_md}\n\n"
                
                # Use strict content boundaries to prevent prompt injection
                user_prompt += f"<<<DOCUMENT_PAGE_CONTENT>>>\n{page_text[:4000]}\n<<<END_DOCUMENT_PAGE_CONTENT>>>"
                
                response = self.llm.chat_json(FACT_EXTRACTION_SYSTEM_PROMPT, user_prompt)
                raw_facts = response.get("facts", [])
                
                processed_facts = []
                for f in raw_facts:
                    quote = f.get("exact_quote", "").strip()
                    start_off, end_off, bbox = PDFProcessor.locate_quote_with_bbox(page_text, blocks, quote)
                    
                    processed_facts.append({
                        "id": f"fact-{uuid.uuid4().hex[:10]}",
                        "document_id": doc_id,
                        "page_number": page_number,
                        "category": f.get("category", "semantic"),
                        "subject": f.get("subject", "Unspecified Entity"),
                        "predicate": f.get("predicate", "stated"),
                        "value": str(f.get("value", "")),
                        "unit": f.get("unit", ""),
                        "temporal_context": f.get("temporal_context", ""),
                        "scope_context": f.get("scope_context", ""),
                        "exact_quote": quote if quote else page_text[:200].strip(),
                        "char_offset_start": start_off,
                        "char_offset_end": end_off,
                        "bbox": bbox,
                        "confidence": float(f.get("confidence", 0.9)),
                        "is_failure_example": 1 if f.get("is_failure_example") else 0,
                        "failure_notes": f.get("failure_notes", "")
                    })
                return processed_facts
            except Exception as e:
                logger.warning(f"LLM fact extraction failed on page {page_number}: {e}. Falling back to domain-agnostic heuristic extraction.")

        # 2. Domain-Agnostic Heuristic Fallback
        return self._heuristic_extract(doc_id, page_number, page_text, blocks, filename)

    def _heuristic_extract(
        self,
        doc_id: str,
        page_number: int,
        page_text: str,
        blocks: List[Dict[str, Any]],
        filename: str
    ) -> List[Dict[str, Any]]:
        """
        Domain-agnostic quantitative & relational fact extractor that works on ANY document
        (science, history, finance, general text) without hardcoded document names or fixed schemas.
        """
        facts = []
        
        # Split text into sentences
        sentences = re.split(r'(?<=[.!?])\s+', page_text)
        
        for sentence in sentences:
            sentence_clean = sentence.strip()
            if len(sentence_clean) < 25 or len(sentence_clean) > 300:
                continue

            # Pattern: Quantitative metric statement (Number + Unit/Word or Currency/Percentage)
            # Examples:
            # - "The population grew by 14.2% over three years"
            # - "Emperor penguins dive to depths of 535 meters"
            # - "Revenue stood at ₹8,142 Crores in FY24"
            # - "Founded on June 22, 2011 with an initial capital of 500,000"
            quant_matches = re.finditer(
                r'(?:([₹$€£]\s*[0-9,]+(?:\.[0-9]+)?(?:\s*(?:Cr(?:ore)?s?|Mn|Million|Billion|Trillion|k|K))?)'
                r'|([0-9,]+(?:\.[0-9]+)?\s*(?:%|percent|Crores|Cr|Millions|Mn|Billion|km|meters|kg|miles|years|days|PIN codes|locations|shares|employees)))',
                sentence_clean,
                re.IGNORECASE
            )

            for m in quant_matches:
                matched_val = m.group(0).strip()
                
                # Extract value and unit
                num_part = re.search(r'[0-9,]+(?:\.[0-9]+)?', matched_val)
                val_str = num_part.group(0).replace(',', '') if num_part else matched_val
                
                unit_str = ""
                if "₹" in matched_val or "rs" in matched_val.lower():
                    unit_str = "INR " + re.sub(r'[^a-zA-Z]', '', matched_val).replace('rs', '').strip()
                elif "$" in matched_val:
                    unit_str = "USD"
                elif "%" in matched_val or "percent" in matched_val.lower():
                    unit_str = "%"
                else:
                    unit_words = re.findall(r'[a-zA-Z]+', matched_val)
                    unit_str = " ".join(unit_words) if unit_words else ""

                # Infer subject from leading clause
                lead_clause = sentence_clean[:m.start()].strip()
                # Clean punctuation from subject
                subject_tokens = [w for w in re.findall(r'[A-Za-z0-9\'-]+', lead_clause) if len(w) > 1]
                if subject_tokens:
                    # Pick last 3-6 informative words before the number as predicate/subject
                    subject_cand = " ".join(subject_tokens[-5:])
                else:
                    subject_cand = "Quantitative Indicator"

                # Infer temporal context if present (e.g. FY24, 2024, 2011, March 31, Q4)
                temp_match = re.search(r'\b(FY\s*\d{2,4}|Q[1-4](?:\s*FY\d{2,4})?|\d{4}-\d{2,4}|\b(?:19|20)\d{2}\b|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})\b', sentence_clean, re.IGNORECASE)
                temporal = temp_match.group(0) if temp_match else ""

                # Determine category based on context cues
                cat = "semantic"
                s_lower = sentence_clean.lower()
                if any(w in s_lower for w in ["revenue", "income", "profit", "ebitda", "capital", "cost", "crore", "dollar", "inr"]):
                    cat = "financial"
                elif any(w in s_lower for w in ["gdp", "inflation", "cpi", "monetary", "rbi", "imf", "economy", "growth"]):
                    cat = "macroeconomic"
                elif any(w in s_lower for w in ["founded", "incorporated", "board", "director", "cin", "company", "registered"]):
                    cat = "corporate_governance"
                elif any(w in s_lower for w in ["volume", "centers", "fleet", "pincode", "hubs", "capacity", "parcels", "delivery"]):
                    cat = "operational"

                start_off, end_off, bbox = PDFProcessor.locate_quote_with_bbox(page_text, blocks, sentence_clean)

                facts.append({
                    "id": f"fact-{uuid.uuid4().hex[:10]}",
                    "document_id": doc_id,
                    "page_number": page_number,
                    "category": cat,
                    "subject": subject_cand,
                    "predicate": "reported_value",
                    "value": val_str,
                    "unit": unit_str.strip(),
                    "temporal_context": temporal,
                    "scope_context": "Reported" if "reported" in s_lower else "General",
                    "exact_quote": sentence_clean,
                    "char_offset_start": start_off,
                    "char_offset_end": end_off,
                    "bbox": bbox,
                    "confidence": 0.82,
                    "is_failure_example": 0,
                    "failure_notes": ""
                })

                if len(facts) >= 6:
                    break

            if len(facts) >= 6:
                break

        return facts
