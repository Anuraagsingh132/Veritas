# 3-Minute Video Demo Script & Guide

> **Assignment Requirement:**  
> *"Link to a demo video of 3 minutes or less showing a PDF being processed and the four required cases above."*

Follow this exact walkthrough to record your 3-minute video.

---

### Timing Breakdown (Total: ~2m 45s)

| Time | Screen / Tab | What to Show & Say |
|------|--------------|-------------------|
| **0:00 - 0:25** | **Showcase View (Landing Page)** | **Introduction**: Open `http://127.0.0.1:8000`. Introduce the **Superjoin Fact Knowledge Layer** built for the VIT 2026 hiring assignment. Mention the tech stack: FastAPI, PyMuPDF, Groq LLM with dynamic auto-discovery & rule-based epistemological heuristics, SQLite with WAL mode, and React with spatial evidence grounding. |
| **0:25 - 1:15** | **4 Required Cases (Showcase View)** | **Walk through each of the 4 evaluated cases**: <br>• **Case 1 (Corroboration)**: Show Delhivery FY24 Consolidated Revenue affirmed between Annual Report Page 36 (₹81,415.38 Million) and Q4 Presentation Page 6 (₹8,142 Crores). Explain the automated Million-to-Crore unit normalization (0.0056% diff, < 1% tolerance).<br>• **Case 2 (Genuine Contradiction)**: Show RBI projecting 6.5% (Annual Report Page 17) vs IMF projecting 6.6% (Article IV Page 13) for FY26 India Real GDP Growth. Explain genuine institutional baseline divergence (10 bps).<br>• **Case 3 (Apparent Contradiction Reconciled by Context)**: Show Delhivery Standalone Revenue from Operations (Annual Report Page 22, ₹74,540.82 Million) vs Consolidated Revenue (Q4 Presentation Page 6, ₹8,142 Crores). Explain how the system uses context (parent company standalone operations vs whole group subsidiaries) to reconcile the figures.<br>• **Case 4 (Extraction/Reasoning Failure & Mitigation)**: Show the RBI appendix table case (Page 89, Table II.7.4 External Vulnerability Indicators) where multi-year column tiers risk header transposition, and explain how the system mitigates it with coordinate table bounding (`find_tables()`). |
| **1:15 - 1:45** | **Fact Explorer** | Click the **Fact Explorer** tab. Show the search bar filtering facts in real-time. Click on category pills (Financial, Macroeconomic, Operational, Governance, Scientific). Click on a fact card to open the **Verbatim Source Evidence Grounding** modal, demonstrating verified page numbers, character offsets, spatial bounding boxes, and exact source text. |
| **1:45 - 2:15** | **Cross-Doc Reconciliation** | Click **Cross-Doc Reconciliation**. Filter by *Corroborations*, *Genuine Contradictions*, and *Contextual Reconciliations*. Highlight the side-by-side evidence cards and the explicit **System Reasoning** generated for each relationship, noting the entity isolation guard that prevents false cross-entity links. |
| **2:15 - 2:40** | **PDF Ingestion (Live Processing)** | Click **PDFs & Ingestion**. Drag and drop any PDF (e.g. from `starter-datasets/` or an external PDF). Watch the live processing indicator extract text and tables, generate structured facts, and perform **incremental reconciliation** against existing knowledge without rebuilding the database. |
| **2:40 - 2:55** | **Wrap-up** | Conclude by showing the `/docs` Swagger API endpoint, mentioning that the system operates both with Groq LLM and completely offline out-of-the-box. Thank the evaluation team. |

---

### Checklist Before Recording
1. Start the server: `python main.py` (or `py main.py` on Windows) inside `backend/`.
2. Open `http://127.0.0.1:8000` in your browser.
3. Have screen recorder ready (OBS Studio, Loom, or Windows Game Bar `Win + G`).
4. Ensure video length is strictly under 3 minutes (180 seconds).
