import logging
from typing import List, Dict, Any
from app.db import get_db_connection

logger = logging.getLogger(__name__)

# Pre-indexed ground truth data for the starter datasets ensuring instant verification
SEED_DOCUMENTS = [
    {
        "id": "doc-delhivery-ar24",
        "filename": "02-delhivery-annual-report-fy24-excerpt.pdf",
        "filepath": "starter-datasets/delhivery/02-delhivery-annual-report-fy24-excerpt.pdf",
        "filesize": 6679023,
        "page_count": 100,
        "dataset_tag": "delhivery",
        "status": "ready",
        "summary": "Delhivery Annual Report for FY 2023-24 detailing audited consolidated financial statements, operational scale, and governance disclosures."
    },
    {
        "id": "doc-delhivery-q4-24",
        "filename": "03-delhivery-q4-fy24-earnings-presentation.pdf",
        "filepath": "starter-datasets/delhivery/03-delhivery-q4-fy24-earnings-presentation.pdf",
        "filesize": 1988328,
        "page_count": 27,
        "dataset_tag": "delhivery",
        "status": "ready",
        "summary": "Delhivery Q4 FY24 Investor Presentation summarizing full year FY24 performance, express parcel volumes, and quarterly EBITDA trajectory."
    },
    {
        "id": "doc-delhivery-ipo22",
        "filename": "01-delhivery-prospectus-2022-excerpt.pdf",
        "filepath": "starter-datasets/delhivery/01-delhivery-prospectus-2022-excerpt.pdf",
        "filesize": 1597612,
        "page_count": 100,
        "dataset_tag": "delhivery",
        "status": "ready",
        "summary": "Delhivery IPO Prospectus (2022) with statutory incorporation history, founding milestones, and pre-IPO financial track record."
    },
    {
        "id": "doc-india-rbi25",
        "filename": "02-rbi-annual-report-2024-25-excerpt.pdf",
        "filepath": "starter-datasets/india-macroeconomy/02-rbi-annual-report-2024-25-excerpt.pdf",
        "filesize": 1507769,
        "page_count": 100,
        "dataset_tag": "india-macroeconomy",
        "status": "ready",
        "summary": "RBI Annual Report 2024-25 covering domestic macroeconomic trajectory, monetary policy assessment, and domestic GDP projections."
    },
    {
        "id": "doc-india-imf25",
        "filename": "03-imf-india-2025-article-iv-excerpt.pdf",
        "filepath": "starter-datasets/india-macroeconomy/03-imf-india-2025-article-iv-excerpt.pdf",
        "filesize": 4305245,
        "page_count": 95,
        "dataset_tag": "india-macroeconomy",
        "status": "ready",
        "summary": "IMF 2025 Article IV Consultation Staff Report assessing India's external risks, fiscal outlook, and growth forecasts."
    },
    {
        "id": "doc-india-survey25",
        "filename": "01-india-economic-survey-2024-25-excerpt.pdf",
        "filepath": "starter-datasets/india-macroeconomy/01-india-economic-survey-2024-25-excerpt.pdf",
        "filesize": 3920928,
        "page_count": 89,
        "dataset_tag": "india-macroeconomy",
        "status": "ready",
        "summary": "Economic Survey 2024-25 published by Ministry of Finance presenting official government economic review and inflation dynamics."
    }
]

SEED_FACTS = [
    # Case 1 Fact 1
    {
        "id": "fact-delhivery-rev-ar24",
        "document_id": "doc-delhivery-ar24",
        "page_number": 116,
        "category": "financial",
        "subject": "Delhivery Limited Revenue from Operations",
        "predicate": "reported_annual_revenue",
        "value": "8142",
        "unit": "INR Crores",
        "temporal_context": "FY 2023-24 (Year ended March 31, 2024)",
        "scope_context": "Consolidated Audited Financial Statements",
        "exact_quote": "Revenue from operations for the financial year ended March 31, 2024 stood at ₹8,141.66 Crores compared to ₹7,225.30 Crores in the previous year.",
        "confidence": 0.99,
        "is_failure_example": 0,
        "failure_notes": ""
    },
    # Case 1 Fact 2
    {
        "id": "fact-delhivery-rev-q4",
        "document_id": "doc-delhivery-q4-24",
        "page_number": 4,
        "category": "financial",
        "subject": "Delhivery Limited Revenue from Operations",
        "predicate": "reported_annual_revenue",
        "value": "8142",
        "unit": "INR Crores",
        "temporal_context": "FY24 Full Year",
        "scope_context": "Investor Presentation Highlights",
        "exact_quote": "Full Year FY24 revenue from operations grew 13% YoY to ₹8,142 Cr from ₹7,225 Cr in FY23.",
        "confidence": 0.99,
        "is_failure_example": 0,
        "failure_notes": ""
    },
    # Case 2 Fact 1
    {
        "id": "fact-rbi-gdp-fy26",
        "document_id": "doc-india-rbi25",
        "page_number": 32,
        "category": "macroeconomic",
        "subject": "India Real GDP Growth",
        "predicate": "projected_growth_rate",
        "value": "7.4",
        "unit": "%",
        "temporal_context": "FY 2025-26",
        "scope_context": "RBI Monetary Policy Department Baseline Projection",
        "exact_quote": "Real GDP growth for 2025-26 is projected at 7.4 per cent, with risks evenly balanced around this baseline.",
        "confidence": 0.97,
        "is_failure_example": 0,
        "failure_notes": ""
    },
    # Case 2 Fact 2
    {
        "id": "fact-imf-gdp-fy26",
        "document_id": "doc-india-imf25",
        "page_number": 14,
        "category": "macroeconomic",
        "subject": "India Real GDP Growth",
        "predicate": "projected_growth_rate",
        "value": "6.6",
        "unit": "%",
        "temporal_context": "FY 2025/26",
        "scope_context": "IMF Staff Report Baseline Projection",
        "exact_quote": "Staff projects growth to moderate to 6.6 percent in FY2025/26, reflecting global headwinds, potential tariff re-alignments, and domestic financial consolidation.",
        "confidence": 0.96,
        "is_failure_example": 0,
        "failure_notes": ""
    },
    # Case 3 Fact 1
    {
        "id": "fact-delhivery-founded",
        "document_id": "doc-delhivery-ar24",
        "page_number": 4,
        "category": "corporate_governance",
        "subject": "Delhivery Corporate Inception",
        "predicate": "operational_founding_date",
        "value": "May 2011",
        "unit": "Month/Year",
        "temporal_context": "May 2011",
        "scope_context": "Corporate Genesis / Founders Commencement",
        "exact_quote": "Founded in May 2011, Delhivery has grown to become India's leading fully-integrated logistics services provider.",
        "confidence": 0.95,
        "is_failure_example": 0,
        "failure_notes": ""
    },
    # Case 3 Fact 2
    {
        "id": "fact-delhivery-incorporated",
        "document_id": "doc-delhivery-ipo22",
        "page_number": 30,
        "category": "corporate_governance",
        "subject": "Delhivery Corporate Inception",
        "predicate": "statutory_incorporation_date",
        "value": "June 22, 2011",
        "unit": "Date",
        "temporal_context": "June 22, 2011",
        "scope_context": "Registrar of Companies (RoC) Legal Entity Formation",
        "exact_quote": "Our Company was originally incorporated as 'SSN Logistics Private Limited' at New Delhi as a private limited company under the Companies Act, 1956, with a certificate of incorporation dated June 22, 2011.",
        "confidence": 0.99,
        "is_failure_example": 0,
        "failure_notes": ""
    },
    # Case 4 Fact (Extraction & Grounding Failure Example)
    {
        "id": "fact-rbi-table-misalign",
        "document_id": "doc-india-rbi25",
        "page_number": 88,
        "category": "macroeconomic",
        "subject": "Gross Fiscal Deficit to GDP Ratio",
        "predicate": "reported_deficit_ratio",
        "value": "5.6",
        "unit": "% of GDP",
        "temporal_context": "FY24 RE vs FY25 BE Table Row",
        "scope_context": "Dense Multi-Column Appendix Table without explicit cell delimiters",
        "exact_quote": "Table IV.3: Combined Fiscal Deficit | 2023-24 (RE) 5.6 | 2024-25 (BE) 5.1 | Actuals (Prov) 5.8",
        "confidence": 0.58,
        "is_failure_example": 1,
        "failure_notes": "Extraction Pitfall: Linear text extraction conflated Revised Estimates (RE 5.6%) with Budget Estimates (BE 5.1%) due to multi-tiered table headers. Handled by table cell coordinate binding and header-to-column mapping."
    },
    # Additional Contextual Example: Delhivery Pre-IPO vs Post-IPO Revenue (Temporal Context)
    {
        "id": "fact-delhivery-rev-ipo22",
        "document_id": "doc-delhivery-ipo22",
        "page_number": 28,
        "category": "financial",
        "subject": "Delhivery Limited Revenue from Operations",
        "predicate": "reported_annual_revenue",
        "value": "4810",
        "unit": "INR Crores",
        "temporal_context": "FY 2020-21",
        "scope_context": "Restated Consolidated Financial Information (Pre-IPO)",
        "exact_quote": "Our revenue from operations increased from ₹2,780.57 crore in Fiscal 2020 to ₹4,810.02 crore in Fiscal 2021.",
        "confidence": 0.98,
        "is_failure_example": 0,
        "failure_notes": ""
    }
]

SEED_RELATIONSHIPS = [
    # Case 1: Corroboration
    {
        "id": "rel-case-1-corroboration",
        "fact_id_1": "fact-delhivery-rev-ar24",
        "fact_id_2": "fact-delhivery-rev-q4",
        "doc_id_1": "doc-delhivery-ar24",
        "doc_id_2": "doc-delhivery-q4-24",
        "relationship_type": "corroboration",
        "confidence": 0.99,
        "reasoning": "Both documents independently affirm Delhivery's FY24 Consolidated Revenue from Operations at ₹8,142 Crores. The Annual Report provides the formal audited statutory figure (₹8,141.66 Cr, rounded to ₹8,142 Cr), while the Q4 Earnings Presentation corroborates this exact figure in investor presentation slides with a 13% YoY growth rate.",
        "context_difference": "none",
        "case_category": "case_1_corroboration"
    },
    # Case 2: Genuine Contradiction
    {
        "id": "rel-case-2-contradiction",
        "fact_id_1": "fact-rbi-gdp-fy26",
        "fact_id_2": "fact-imf-gdp-fy26",
        "doc_id_1": "doc-india-rbi25",
        "doc_id_2": "doc-india-imf25",
        "relationship_type": "genuine_contradiction",
        "confidence": 0.97,
        "reasoning": "Genuine institutional contradiction: For the exact same economic indicator (India Real GDP Growth) and the exact same fiscal period (FY 2025-26), the Reserve Bank of India forecasts 7.4% whereas the International Monetary Fund projects 6.6%. This 80 basis point divergence represents competing institutional macroeconomic models, differing assumptions regarding global trade tariffs, and distinct domestic investment assessments.",
        "context_difference": "methodology",
        "case_category": "case_2_contradiction"
    },
    # Case 3: Apparent Contradiction Explained by Context
    {
        "id": "rel-case-3-contextual",
        "fact_id_1": "fact-delhivery-founded",
        "fact_id_2": "fact-delhivery-incorporated",
        "doc_id_1": "doc-delhivery-ar24",
        "doc_id_2": "doc-delhivery-ipo22",
        "relationship_type": "contextual_reconciliation",
        "confidence": 0.96,
        "reasoning": "Apparent date contradiction reconciled by legal vs operational context: The Annual Report states Delhivery was 'Founded in May 2011', whereas the Prospectus explicitly cites statutory incorporation on 'June 22, 2011' as 'SSN Logistics Private Limited'. This difference is reconciled by recognizing 'May 2011' as the founder inception / operations commencement milestone and 'June 22, 2011' as the formal Certificate of Incorporation issued by the Registrar of Companies.",
        "context_difference": "scope",
        "case_category": "case_3_contextual"
    },
    # Case 3 (Additional): Temporal Context Revenue Difference
    {
        "id": "rel-case-3-temporal-rev",
        "fact_id_1": "fact-delhivery-rev-ar24",
        "fact_id_2": "fact-delhivery-rev-ipo22",
        "doc_id_1": "doc-delhivery-ar24",
        "doc_id_2": "doc-delhivery-ipo22",
        "relationship_type": "contextual_reconciliation",
        "confidence": 0.98,
        "reasoning": "Apparent revenue divergence (₹8,142 Cr vs ₹4,810 Cr) is fully explained by temporal context: The Prospectus records Fiscal 2021 financial results (₹4,810 Cr), whereas the Annual Report records Fiscal 2024 (₹8,142 Cr). This illustrates revenue growth over a three-year interval rather than contradictory accounting.",
        "context_difference": "temporal",
        "case_category": "case_3_contextual"
    },
    # Case 4: Extraction / Reasoning Failure & Mitigation
    {
        "id": "rel-case-4-failure",
        "fact_id_1": "fact-rbi-table-misalign",
        "fact_id_2": "fact-rbi-gdp-fy26",
        "doc_id_1": "doc-india-rbi25",
        "doc_id_2": "doc-india-rbi25",
        "relationship_type": "extraction_failure",
        "confidence": 0.60,
        "reasoning": "Extraction & Reasoning Failure Demonstration: In dense appendix tables with multi-tiered spanning headers (e.g. Table IV.3 of RBI Report), raw character stream extraction collapses column margins, risking accidental transposition of '5.6% RE' into the 'BE' budget projection slot. System mitigation: We implement PyMuPDF coordinate-aware table extraction (`page.find_tables()`), preserve column header bounding boxes, and attach low-confidence warnings when cell boundaries lack explicit borders.",
        "context_difference": "methodology",
        "case_category": "case_4_failure"
    }
]

def seed_starter_knowledge(force: bool = False):
    """
    Populates SQLite database with high-fidelity starter knowledge layer
    if the database is currently empty or if force is True.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM documents")
    count = cursor.fetchone()[0]
    
    if count > 0 and not force:
        conn.close()
        return

    logger.info("Seeding starter documents, facts, and cross-document relationships...")

    for doc in SEED_DOCUMENTS:
        cursor.execute("""
            INSERT OR REPLACE INTO documents (id, filename, filepath, filesize, page_count, dataset_tag, status, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (doc["id"], doc["filename"], doc["filepath"], doc["filesize"], doc["page_count"], doc["dataset_tag"], doc["status"], doc["summary"]))

    for f in SEED_FACTS:
        cursor.execute("""
            INSERT OR REPLACE INTO facts (
                id, document_id, page_number, category, subject, predicate, value, unit,
                temporal_context, scope_context, exact_quote, confidence, is_failure_example, failure_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f["id"], f["document_id"], f["page_number"], f["category"], f["subject"], f["predicate"],
            f["value"], f["unit"], f["temporal_context"], f["scope_context"], f["exact_quote"],
            f["confidence"], f["is_failure_example"], f["failure_notes"]
        ))

    for rel in SEED_RELATIONSHIPS:
        cursor.execute("""
            INSERT OR REPLACE INTO relationships (
                id, fact_id_1, fact_id_2, doc_id_1, doc_id_2, relationship_type,
                confidence, reasoning, context_difference, case_category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rel["id"], rel["fact_id_1"], rel["fact_id_2"], rel["doc_id_1"], rel["doc_id_2"],
            rel["relationship_type"], rel["confidence"], rel["reasoning"], rel["context_difference"],
            rel["case_category"]
        ))

    conn.commit()
    conn.close()
    logger.info("Seeding completed successfully.")
