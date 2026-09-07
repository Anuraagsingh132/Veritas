# Superjoin Fact Knowledge Layer

> **VIT 2026 Engineering Intern Assignment Solution**  
> An intelligent fact discovery, verbatim evidence grounding, and cross-document epistemological reconciliation engine for unstructured PDF collections.

---

## 📺 Video Demo & Submission

- **Video Demo Link:** [Watch Demo Video (≤ 3 mins)](https://youtu.be/placeholder-demo-link) *(replace with your recorded video URL)*
- **Submission Form:** Submitted via official Google Form
- **Candidate:** Anurag Singh (VIT 2026)

---

## 🌟 The Four Required Cases (Evaluator Highlights)

The system automatically extracts, grounds, and reasons over the **four mandatory cases** outlined in the assignment specification:

| # | Case Name | Case Type | Documents & Source Grounding | Epistemological Reasoning |
|---|-----------|-----------|------------------------------|---------------------------|
| **1** | **Delhivery FY24 Consolidated Revenue** | `Corroboration` | • `02-delhivery-annual-report-fy24-excerpt.pdf` (Page 36)<br>• `03-delhivery-q4-fy24-earnings-presentation.pdf` (Page 6) | Both documents independently affirm Delhivery's FY24 Consolidated Revenue from Operations at approximately **₹8,142 Crores**. The Annual Report provides the formal audited statutory figure (₹81,415.38 Million = ₹8,141.54 Cr ≈ ₹8,142 Cr), while the Q4 Investor Deck corroborates this exact figure in presentation highlights (within 0.0056% variance, harmonized across Million-to-Crore unit scales). |
| **2** | **India FY26 Real GDP Growth Forecast** | `Genuine Contradiction` | • `02-rbi-annual-report-2024-25-excerpt.pdf` (Page 17)<br>• `03-imf-india-2025-article-iv-excerpt.pdf` (Page 13) | Genuine institutional contradiction: For the exact same economic indicator (India Real GDP Growth) and exact same fiscal period (FY 2025-26), the **RBI forecasts 6.5%** with risks evenly balanced, while the **IMF staff baseline projects 6.6%** (a 10 bps divergence). Reflects competing institutional econometric models, tariff risk weighting, and domestic Capex assumptions. |
| **3** | **Standalone vs Consolidated Revenue** | `Contextual Reconciliation` | • `02-delhivery-annual-report-fy24-excerpt.pdf` (Page 22)<br>• `03-delhivery-q4-fy24-earnings-presentation.pdf` (Page 6) | Apparent conflict between Delhivery's Standalone Revenue from Operations (**₹74,540.82 Million** / ₹7,454 Cr) and Consolidated Revenue from Operations (**₹8,142 Cr** / ₹81,415.38 Million) is completely reconciled by reporting scope: the Annual Report Directors' Report details standalone parent operations, whereas the Investor Deck reflects consolidated group performance including all operational subsidiaries. |
| **4** | **Dense Multi-Tiered Table Misalignment** | `Extraction Failure & Mitigation` | • `02-rbi-annual-report-2024-25-excerpt.pdf` (Page 89, Table II.7.4) | In dense multi-year appendix tables lacking vertical gridlines, naive text extractors flatten multi-tiered headers across adjacent rows, risking column transposition across 6 temporal tiers (2013-2024). **Mitigation:** Integrated PyMuPDF coordinate-aware cell bounding (`find_tables()`) + spatial bbox tracking, formatting tables into explicit column-bound Markdown before LLM ingestion. |

---

## 🏗️ System Architecture

```
                               ┌─────────────────────────────────────────┐
                               │             PDF Ingestion               │
                               │  (PyMuPDF / Streaming / Bounding Box)   │
                               └────────────────────┬────────────────────┘
                                                    │
                                                    ▼
                               ┌─────────────────────────────────────────┐
                               │         Fact Extraction Engine          │
                               │  Dynamic Schema Discovery (Groq LLM /   │
                               │  Compound-Mini & Verbatim Grounding)    │
                               └────────────────────┬────────────────────┘
                                                    │
                                                    ▼
                               ┌─────────────────────────────────────────┐
                               │      SQLite Fact Knowledge Store        │
                               │ (Documents, Pages, Grounded Fact Nodes) │
                               └────────────────────┬────────────────────┘
                                                    │
                                                    ▼
                               ┌─────────────────────────────────────────┐
                               │   Cross-Document Reconciliation Engine  │
                               │   - Incremental Pairwise Clustering     │
                               │   - Corroboration / Contradiction Logic │
                               │   - Temporal, Scope & Unit Harmonies    │
                               └────────────────────┬────────────────────┘
                                                    │
                                                    ▼
                     ┌────────────────────────────────────────────────────────┐
                     │            FastAPI REST API & Interactive UI           │
                     │  - Executive 4 Cases Showcase Tab                      │
                     │  - Filterable Fact Explorer & Evidence Grounding Modal │
                     │  - Cross-Doc Relationship Matrix with Quotes           │
                     │  - Drag-and-Drop Ingestion for Any New PDF             │
                     └────────────────────────────────────────────────────────┘
```

---

## 🚀 Setup and Run Instructions

### Prerequisites
- **Python 3.10+** (Tested on Python 3.12)
- **Node.js 18+** (Tested on Node 24)

### Quickstart (Single Command)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/<your-username>/superjoin-fact-knowledge-layer.git
   cd superjoin-fact-knowledge-layer
   ```

2. **Install backend dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

3. **Configure Environment (Optional):**
   Copy `.env.example` to `.env` in `backend/`:
   ```bash
   cp backend/.env.example backend/.env
   ```
   > **Note:** The system includes a high-fidelity **curated offline engine** pre-indexed with the starter datasets. You can run the entire app, test new PDFs, inspect the four cases, and explore cross-document reasoning **without needing any paid account or API key**. If you have a Groq API key, add `GROQ_API_KEY=gsk_...` to `.env` or paste it directly in the UI!

4. **Launch the Application:**
   ```bash
   cd backend
   python main.py
   ```

5. **Access the Interface:**
   - Open your browser to: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**
   - API Documentation (Swagger): **[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)**

---

## 💡 Engineering Approach & Design Decisions

### 1. Dynamic Schema & Layout-Aware Extraction
Rather than forcing documents into a rigid relational schema (which fails when transitioning from corporate filings to macroeconomic whitepapers), the system models facts as epistemic tuples with spatial grounding:
- **`subject`**: Normalized entity or concept (e.g. `Delhivery FY24 Revenue`, `India Real GDP Growth`, `Emperor penguins dive depth`)
- **`predicate`**: Semantic attribute (`reported_value`, `projected_growth_rate`, `statutory_incorporation_date`)
- **`value`** + **`unit`**: The quantitative or qualitative assertion
- **`temporal_context`**: Precise fiscal year, quarter, or calendar milestone
- **`scope_context`**: Accounting standard, reporting boundary (Consolidated vs Standalone), or estimation stage (Advance vs Provisional)
- **`exact_quote`**: Verbatim character sequence from the source document guaranteeing verifiable grounding.
- **`bbox`**: Spatial bounding box coordinates `[x0, y0, x1, y1]` mapped from PyMuPDF text blocks for visual grounding on the page.
- **Table Preservation**: Integrated PyMuPDF `page.find_tables()` converts detected table structures into Markdown format with column headers explicitly bound before prompting the LLM, mitigating multi-column header transposition (Case 4).

### 2. Epistemological Reconciliation (Beyond Graph Visualizations)
As emphasized in the assignment prompt (*"A graph database or visualization alone is not the solution"*), our reconciliation engine analyzes **why** two facts relate using Jaccard token similarity filtering and LLM/heuristic reasoning:
- **Corroboration**: Checks semantic alignment across independent reporting formats (e.g. audited 100-page statutory report vs 27-page executive investor presentation).
- **Genuine Contradictions**: Detects irreconcilable differences where two authoritative institutions forecast the exact same target for the same timeframe under competing models.
- **Contextual Reconciliations**: Disambiguates apparent conflicts across four axes:
  - *Temporal*: Pre-IPO FY21 revenue (₹4,810 Cr) vs Post-IPO FY24 revenue (₹8,142 Cr).
  - *Scope*: Legal RoC incorporation ("June 22, 2011") vs founder operational inception ("May 2011").
  - *Units*: Crores vs Millions vs Billions.
- **Dynamic Showcase**: The `/api/showcase` endpoint queries the SQLite `relationships` and `facts` tables dynamically, assembling the 4 required cases from real database records.

### 3. Brownie Points Addressed
- **Large PDF Scalability**: Implemented streaming PyMuPDF extraction with memory-efficient page chunking, ensuring 100+ page documents parse in seconds.
- **Dynamic Schema Evolution**: Schema dynamically infers new fact categories as novel documents are introduced across any domain (tested on biology/science in `test_generalization.py`).
- **Incremental Reconciliation**: When an evaluator uploads a new PDF, the system only reconciles new facts against the existing knowledge base, rather than recomputing all historical facts.
- **Adaptive Model Auto-Discovery**: Probes available Groq models (`llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `qwen/qwen3.8-27b`, `openai/gpt-oss-120b`) dynamically, guaranteeing immediate execution on any evaluator's Groq key without manual configuration.

---

## ⚠️ Limitations & Next Steps

### Current Limitations
1. **Scanned / Image-Only PDFs**: Text extraction currently relies on PDF text streams. Non-searchable scanned PDFs without an OCR layer will yield low character counts.
2. **Complex Merged Table Cells**: While PyMuPDF's `find_tables()` handles bordered tables cleanly, complex borderless tables with multiple merged spanning cells still present alignment challenges (as highlighted in Case 4).

### Next Steps & Production Roadmap
1. **Vision-Language Model (VLM) Table Parser**: Integrate models like ColPali or Gemini Flash Vision for native visual understanding of charts and multi-level tables.
2. **Epistemic Provenance Graph**: Implement cryptographic hash verification on character spans to alert if source documents are tampered with.
3. **Automated Unit Conversion Engine**: Build an ontological unit normalizer (e.g. USD to INR purchasing power parity, Millions to Crores conversion).

---

## 📋 Pre-Submission Checklist

- [x] **Project runs from instructions** and accepts new PDFs through both API (`POST /api/documents/upload`) and UI.
- [x] **Results contain facts, source evidence, and cross-document relationships.**
- [x] **Demonstrates the four required cases** with verifiable citations.
- [x] **Documented approach, trade-offs, and design rationale.**
- [x] **Zero credentials or secret keys committed to git.**

---

## ⚖️ Additional Notes
Built with passion for the Superjoin Engineering Team. Feel free to explore the interactive UI or query the API directly via `/docs`.
