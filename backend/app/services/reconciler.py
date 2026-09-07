import re
import uuid
import hashlib
import logging
from typing import List, Dict, Any, Optional, Tuple, Set
from app.services.llm_client import LLMClient

logger = logging.getLogger(__name__)

RECONCILIATION_SYSTEM_PROMPT = """You are an expert Fact Reconciliation & Epistemology Engine.
Your role is to compare two facts extracted from different documents and classify their epistemological relationship with rigorous reasoning.

Classification Rules:
1. CORROBORATION (Case 1):
   - Both facts independently affirm the exact same reality, even if expressed with different phrasing, rounding, or formatting.
   - Example: Document A reports Delhivery FY24 revenue of ₹8,141.66 Cr, and Document B corroborates this as ₹8,142 Cr in presentation highlights.

2. GENUINE_CONTRADICTION (Case 2):
   - The facts make fundamentally conflicting claims about the SAME subject, for the SAME time horizon, under the SAME scope. They cannot both be true under the same definition.
   - Example: RBI projects India's FY26 GDP growth at 7.4%, whereas IMF Article IV projects 6.6% for the same fiscal year. Competing baseline models and divergent forecasts.

3. CONTEXTUAL_RECONCILIATION (Case 3):
   - The facts appear contradictory or divergent at face value, but the discrepancy is completely explained by context:
     a) Temporal difference (e.g., FY22 baseline vs FY24 outcome, or founding month vs legal incorporation date).
     b) Scope difference (e.g., Consolidated vs Standalone, or Advance Estimate vs Provisional).
     c) Unit/scale difference (e.g., Millions vs Crores).
     d) Legal vs Operational definition (e.g., Company conceptual founding vs statutory incorporation on certificate).

4. EXTRACTION_FAILURE (Case 4):
   - The anomaly or discrepancy arose from a PDF layout artifact, multi-column table transposition, or header alignment error.

5. UNRELATED:
   - The facts describe completely different entities (e.g., Apple revenue vs Microsoft revenue), unrelated topics, or metrics that have no meaningful comparative relationship.
   - Set relationship_type to "unrelated".

Format your response as a JSON object:
{
  "relationship_type": "corroboration | genuine_contradiction | contextual_reconciliation | extraction_failure | unrelated",
  "confidence": 0.95,
  "case_category": "case_1_corroboration | case_2_contradiction | case_3_contextual | case_4_failure | none",
  "context_difference": "temporal | scope | units | methodology | none",
  "reasoning": "Clear, rigorous multi-sentence explanation of why these two facts corroborate, contradict, reconcile, or are unrelated."
}
"""

STOP_WORDS = {
    "the", "and", "of", "in", "to", "for", "a", "an", "is", "was", "by", "on", "at",
    "from", "as", "with", "that", "this", "it", "are", "were", "be", "or", "total",
    "statement", "quantitative", "reported", "metric", "annual", "report", "section",
    "definitions", "summary", "page", "pages"
}

def normalize_numeric_value_and_unit(val_str: Any, unit_str: Any) -> Tuple[Optional[float], str]:
    """
    Normalizes numeric values across Crores and Millions to a standard Crores scale:
    1 Crore = 10 Million -> Value in Millions / 10 = Value in Crores.
    """
    if val_str is None:
        return None, ""
    try:
        clean_val = float(str(val_str).replace(",", "").strip())
    except (ValueError, TypeError):
        return None, str(unit_str or "").lower().strip()

    clean_unit = str(unit_str or "").lower().strip()
    crore_units = {"cr", "crore", "crores", "inr crore", "inr crores", "₹ crore", "₹ cr"}
    million_units = {"m", "mn", "million", "millions", "inr million", "inr millions", "₹ million", "₹ in million", "in million"}

    if any(u in clean_unit for u in million_units):
        return clean_val / 10.0, "crores"
    elif any(u in clean_unit for u in crore_units):
        return clean_val, "crores"
    
    return clean_val, clean_unit

class FactReconciler:
    """
    Cross-document reasoning engine that clusters related facts,
    evaluates relationships, and documents grounded reasoning.
    Limits candidate pairs to top-K to ensure scalability and avoid Groq rate limits.
    """
    def __init__(self, llm_client: Optional[LLMClient] = None, max_candidates: int = 20):
        self.llm = llm_client or LLMClient()
        self.max_candidates = max_candidates

    @staticmethod
    def generate_relationship_id(fact_id_1: str, fact_id_2: str) -> str:
        """Deterministically generates relationship ID based on canonically sorted fact IDs."""
        sorted_pair = sorted([str(fact_id_1), str(fact_id_2)])
        pair_str = f"{sorted_pair[0]}:{sorted_pair[1]}"
        digest = hashlib.sha256(pair_str.encode("utf-8")).hexdigest()[:12]
        return f"rel-{digest}"

    def reconcile_facts(
        self,
        existing_facts: List[Dict[str, Any]],
        new_facts: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs pairwise cross-document reconciliation.
        If new_facts is provided, performs incremental reconciliation.
        Instantly falls back to domain-agnostic heuristics if rate limits are reached.
        """
        candidate_pairs = self._find_candidate_pairs(existing_facts, new_facts)
        logger.info(f"Reconciling {len(candidate_pairs)} candidate fact pairs.")
        
        relationships = []
        skip_llm = False
        for fact_a, fact_b in candidate_pairs:
            rel = None
            if (self.llm and self.llm.is_available() and not skip_llm 
                    and not getattr(self.llm, 'is_rate_limited', lambda: False)()):
                try:
                    rel = self._compare_pair_llm(fact_a, fact_b)
                except Exception as e:
                    err_str = str(e).lower()
                    if "rate limit" in err_str or "429" in err_str or "cooldown" in err_str:
                        logger.warning("Groq rate limit encountered during reconciliation. Switching remaining pairs to fast heuristic reconciliation.")
                        skip_llm = True
                    rel = self._heuristic_reconcile(fact_a, fact_b)
            else:
                rel = self._heuristic_reconcile(fact_a, fact_b)

            if rel:
                relationships.append(rel)
                
        return relationships

    def _find_candidate_pairs(
        self,
        existing_facts: List[Dict[str, Any]],
        new_facts: Optional[List[Dict[str, Any]]] = None
    ) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """
        Identifies candidate fact pairs from DIFFERENT documents that share semantic overlap.
        Uses Jaccard token similarity and category matching, capped at top-K candidates.
        """
        scored_pairs = []
        seen_pairs: Set[Tuple[str, str]] = set()

        if new_facts is not None:
            list_a = new_facts
            list_b = existing_facts
        else:
            list_a = existing_facts
            list_b = existing_facts

        for fa in list_a:
            for fb in list_b:
                if fa["id"] == fb["id"]:
                    continue
                # Only compare facts from DIFFERENT documents
                if fa.get("document_id") == fb.get("document_id"):
                    continue

                # Filter out duplicate uploads of the exact same underlying file
                fn_a = re.sub(r'^doc-[a-f0-9]+_', '', fa.get("document_filename") or fa.get("filename", "")).lower().strip()
                fn_b = re.sub(r'^doc-[a-f0-9]+_', '', fb.get("document_filename") or fb.get("filename", "")).lower().strip()
                if fn_a and fn_b and fn_a == fn_b:
                    continue

                pair_key = tuple(sorted([fa["id"], fb["id"]]))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                # Candidate Pre-Filtering: Protect against comparing incompatible categories or value types
                cat_a = str(fa.get("category", "")).lower().strip()
                cat_b = str(fb.get("category", "")).lower().strip()
                ent_a = str(fa.get("entity", "")).strip()
                ent_b = str(fb.get("entity", "")).strip()

                # Disallow pairing distinct corporate entities
                if ent_a and ent_b and ent_a != "General" and ent_b != "General" and ent_a.lower() != ent_b.lower():
                    if not (cat_a == "macroeconomic" and cat_b == "macroeconomic"):
                        continue

                val_a = str(fa.get("value", "")).strip().replace(",", "")
                val_b = str(fb.get("value", "")).strip().replace(",", "")
                is_num_a = any(c.isdigit() for c in val_a)
                is_num_b = any(c.isdigit() for c in val_b)

                # Do not pair a purely textual list with a numerical metric unless it's a failure example
                if is_num_a != is_num_b and not (fa.get("is_failure_example") or fb.get("is_failure_example")):
                    continue

                # Do not pair disparate non-quantitative categories (e.g. governance vs environmental)
                if cat_a and cat_b and cat_a != cat_b and cat_a != "quantitative" and cat_b != "quantitative":
                    continue

                # Filter out generic fallback subjects to prevent header/footer noise pairings
                sub_a = str(fa.get("subject", "")).strip()
                sub_b = str(fb.get("subject", "")).strip()
                if sub_a in ["Quantitative Statement", "Reported Metric"] or sub_b in ["Quantitative Statement", "Reported Metric"]:
                    continue

                score = self._compute_similarity(fa, fb)
                if score > 0.20:  # Sufficient semantic and entity overlap
                    first, second = (fa, fb) if fa["id"] < fb["id"] else (fb, fa)
                    scored_pairs.append((score, first, second))

        # Sort by similarity score descending and cap at max_candidates
        scored_pairs.sort(key=lambda x: x[0], reverse=True)
        return [(fa, fb) for _, fa, fb in scored_pairs[:self.max_candidates]]

    def _compute_similarity(self, fa: Dict[str, Any], fb: Dict[str, Any]) -> float:
        """
        Calculates token Jaccard similarity between two facts across subject, predicate, entity, and quotes.
        """
        ent_a = str(fa.get("entity", "")).strip()
        ent_b = str(fb.get("entity", "")).strip()
        cat_a = str(fa.get("category", "")).lower().strip()
        cat_b = str(fb.get("category", "")).lower().strip()

        # Reject candidate pairing between different corporate entities
        if ent_a and ent_b and ent_a != "General" and ent_b != "General" and ent_a.lower() != ent_b.lower():
            if not (cat_a == "macroeconomic" and cat_b == "macroeconomic"):
                return 0.0

        text_a = f"{ent_a} {fa.get('subject', '')} {fa.get('predicate', '')} {cat_a}".lower()
        text_b = f"{ent_b} {fb.get('subject', '')} {fb.get('predicate', '')} {cat_b}".lower()

        tokens_a = {w for w in re.findall(r'\b[a-z]{3,}\b', text_a) if w not in STOP_WORDS}
        tokens_b = {w for w in re.findall(r'\b[a-z]{3,}\b', text_b) if w not in STOP_WORDS}

        if not tokens_a or not tokens_b:
            return 0.0

        intersection = len(tokens_a.intersection(tokens_b))
        union = len(tokens_a.union(tokens_b))
        if intersection == 0:
            return 0.0

        jaccard = intersection / union if union > 0 else 0.0

        # Category bonus (toned down to 0.05)
        if fa.get("category") == fb.get("category") and fa.get("category"):
            jaccard += 0.05

        # Temporal match bonus
        if fa.get("temporal_context") and fa.get("temporal_context") == fb.get("temporal_context"):
            jaccard += 0.10

        # Entity match bonus
        if ent_a and ent_a == ent_b:
            jaccard += 0.15

        return jaccard

    def _compare_pair_llm(self, fa: Dict[str, Any], fb: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Classifies relationship using LLM. Returns None if classified as unrelated."""
        if fa["id"] > fb["id"]:
            fa, fb = fb, fa

        rel_id = self.generate_relationship_id(fa["id"], fb["id"])

        prompt = (
            f"Fact 1 (from doc {fa.get('document_id')}):\n"
            f"Entity: {fa.get('entity')}\n"
            f"Subject: {fa.get('subject')}\n"
            f"Predicate: {fa.get('predicate')}\n"
            f"Value: {fa.get('value')} {fa.get('unit', '')}\n"
            f"Temporal: {fa.get('temporal_context')}\n"
            f"Scope: {fa.get('scope_context')}\n"
            f"Quote: \"{fa.get('exact_quote')}\"\n\n"
            f"Fact 2 (from doc {fb.get('document_id')}):\n"
            f"Entity: {fb.get('entity')}\n"
            f"Subject: {fb.get('subject')}\n"
            f"Predicate: {fb.get('predicate')}\n"
            f"Value: {fb.get('value')} {fb.get('unit', '')}\n"
            f"Temporal: {fb.get('temporal_context')}\n"
            f"Scope: {fb.get('scope_context')}\n"
            f"Quote: \"{fb.get('exact_quote')}\""
        )
        res = self.llm.chat_json(RECONCILIATION_SYSTEM_PROMPT, prompt, max_tokens=500)
        rel_type = res.get("relationship_type", "contextual_reconciliation")
        if rel_type == "unrelated":
            return None

        return {
            "id": rel_id,
            "fact_id_1": fa["id"],
            "fact_id_2": fb["id"],
            "doc_id_1": fa["document_id"],
            "doc_id_2": fb["document_id"],
            "relationship_type": rel_type,
            "confidence": float(res.get("confidence", 0.9)),
            "reasoning": res.get("reasoning", "Semantic analysis across independent documents."),
            "context_difference": res.get("context_difference", ""),
            "case_category": res.get("case_category", "")
        }

    def _compare_pair(self, fa: Dict[str, Any], fb: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Classifies relationship using LLM (if available) or domain-agnostic epistemological rules.
        """
        if self.llm.is_available() and not getattr(self.llm, 'is_rate_limited', lambda: False)():
            try:
                res = self._compare_pair_llm(fa, fb)
                if res is not None:
                    return res
                return None
            except Exception as e:
                logger.warning(f"LLM reconciliation call failed: {e}. Falling back to rule-based reconciliation.")

        return self._heuristic_reconcile(fa, fb)

    def _heuristic_reconcile(self, fa: Dict[str, Any], fb: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Rigorous, domain-agnostic epistemological rules that work across any topic:
        - Exact numeric/semantic match -> Corroboration
        - Differing values + distinct time periods/units/scopes -> Contextual Reconciliation
        - Conflicting values + identical time period & scope -> Genuine Contradiction
        Strictly enforces entity isolation and subject overlap guards.
        """
        if fa["id"] > fb["id"]:
            fa, fb = fb, fa

        rel_id = self.generate_relationship_id(fa["id"], fb["id"])

        ent_a = str(fa.get("entity", "")).strip()
        ent_b = str(fb.get("entity", "")).strip()
        sub_a = str(fa.get("subject", "")).strip()
        sub_b = str(fb.get("subject", "")).strip()
        cat_a = str(fa.get("category", "")).lower().strip()
        cat_b = str(fb.get("category", "")).lower().strip()

        # Non-stopword tokens from entity + subject
        tokens_subj_a = {w for w in re.findall(r'\b[a-z]{3,}\b', f"{ent_a} {sub_a}".lower()) if w not in STOP_WORDS}
        tokens_subj_b = {w for w in re.findall(r'\b[a-z]{3,}\b', f"{ent_b} {sub_b}".lower()) if w not in STOP_WORDS}

        # Check for matching entity
        same_entity = (ent_a and ent_b and ent_a.lower() == ent_b.lower())

        # Macroeconomic institutional comparison (e.g. RBI vs IMF comparing India GDP)
        is_macro_comparison = (cat_a == "macroeconomic" and cat_b == "macroeconomic") and \
            any(w in f"{sub_a} {sub_b}".lower() for w in ["gdp", "growth", "india", "inflation", "debt", "deficit"])

        has_subject_overlap = len(tokens_subj_a.intersection(tokens_subj_b)) > 0 or sub_a.lower() == sub_b.lower()

        # Entity Guard: Strictly reject comparisons between different corporate entities
        if ent_a and ent_b and ent_a != "General" and ent_b != "General" and not same_entity and not is_macro_comparison:
            return None

        # Require subject overlap, confirmed same entity, or macroeconomic comparison
        if not has_subject_overlap and not same_entity and not is_macro_comparison:
            return None

        val_a = str(fa.get("value", "")).strip().replace(",", "")
        val_b = str(fb.get("value", "")).strip().replace(",", "")
        temp_a = str(fa.get("temporal_context", "")).strip().lower()
        temp_b = str(fb.get("temporal_context", "")).strip().lower()
        unit_a = str(fa.get("unit", "")).strip().lower()
        unit_b = str(fb.get("unit", "")).strip().lower()
        scope_a = str(fa.get("scope_context", "")).strip().lower()
        scope_b = str(fb.get("scope_context", "")).strip().lower()

        num_a, norm_unit_a = normalize_numeric_value_and_unit(val_a, unit_a)
        num_b, norm_unit_b = normalize_numeric_value_and_unit(val_b, unit_b)

        # Check for Extraction Failure flag (Case 4)
        if fa.get("is_failure_example") or fb.get("is_failure_example"):
            failure_fact = fa if fa.get("is_failure_example") else fb
            return {
                "id": rel_id,
                "fact_id_1": fa["id"],
                "fact_id_2": fb["id"],
                "doc_id_1": fa["document_id"],
                "doc_id_2": fb["document_id"],
                "relationship_type": "extraction_failure",
                "confidence": 0.88,
                "reasoning": failure_fact.get("failure_notes") or "Document layout complexity produced parsing divergence.",
                "context_difference": "methodology",
                "case_category": "case_4_failure"
            }

        # Case 1: Corroboration (exact value equality or normalized numeric difference <= 1% due to rounding/unit scale)
        if num_a is not None and num_b is not None:
            denom = max(abs(num_a), abs(num_b))
            if abs(num_a - num_b) < 1e-4 or (denom > 0 and abs(num_a - num_b) / denom < 0.01):
                return {
                    "id": rel_id,
                    "fact_id_1": fa["id"],
                    "fact_id_2": fb["id"],
                    "doc_id_1": fa["document_id"],
                    "doc_id_2": fb["document_id"],
                    "relationship_type": "corroboration",
                    "confidence": 0.95,
                    "reasoning": f"Both documents independently affirm the value of {fa.get('subject')} at approximately '{val_a} {fa.get('unit', '')}' (normalized: {num_a:.2f} {norm_unit_a}), confirming ground truth across independent publications.",
                    "context_difference": "none",
                    "case_category": "case_1_corroboration"
                }
        elif val_a and val_a == val_b:
            return {
                "id": rel_id,
                "fact_id_1": fa["id"],
                "fact_id_2": fb["id"],
                "doc_id_1": fa["document_id"],
                "doc_id_2": fb["document_id"],
                "relationship_type": "corroboration",
                "confidence": 0.95,
                "reasoning": f"Both sources report the identical assertion '{val_a}' for {fa.get('subject')}.",
                "context_difference": "none",
                "case_category": "case_1_corroboration"
            }

        # Case 3: Contextual Reconciliation via Scope Difference (e.g. Standalone vs Consolidated)
        is_scope_diff = (scope_a and scope_b and scope_a != scope_b) or \
                        ("standalone" in scope_a and "consolidated" in scope_b) or \
                        ("consolidated" in scope_a and "standalone" in scope_b) or \
                        ("standalone" in (fa.get("subject", "") + fa.get("exact_quote", "")).lower() and \
                         "consolidated" in (fb.get("subject", "") + fb.get("exact_quote", "")).lower()) or \
                        ("consolidated" in (fa.get("subject", "") + fa.get("exact_quote", "")).lower() and \
                         "standalone" in (fb.get("subject", "") + fb.get("exact_quote", "")).lower())

        if is_scope_diff:
            scope_desc_a = "Standalone" if "standalone" in (scope_a + fa.get("subject", "") + fa.get("exact_quote", "")).lower() else (scope_a or "Reported")
            scope_desc_b = "Consolidated" if "consolidated" in (scope_b + fb.get("subject", "") + fb.get("exact_quote", "")).lower() else (scope_b or "Reported")
            return {
                "id": rel_id,
                "fact_id_1": fa["id"],
                "fact_id_2": fb["id"],
                "doc_id_1": fa["document_id"],
                "doc_id_2": fb["document_id"],
                "relationship_type": "contextual_reconciliation",
                "confidence": 0.94,
                "reasoning": f"Apparent conflict is resolved by reporting scope: Document A reflects {scope_desc_a} operations ('{val_a} {fa.get('unit', '')}') whereas Document B reflects {scope_desc_b} group performance ('{val_b} {fb.get('unit', '')}'). Both figures are valid within their respective accounting boundaries.",
                "context_difference": "scope",
                "case_category": "case_3_contextual"
            }

        # Case 3: Contextual Reconciliation via Temporal Difference
        if temp_a and temp_b and temp_a != temp_b:
            return {
                "id": rel_id,
                "fact_id_1": fa["id"],
                "fact_id_2": fb["id"],
                "doc_id_1": fa["document_id"],
                "doc_id_2": fb["document_id"],
                "relationship_type": "contextual_reconciliation",
                "confidence": 0.92,
                "reasoning": f"The divergence between {val_a} ({fa.get('unit', '')}) and {val_b} ({fb.get('unit', '')}) is reconciled by temporal context: Document A measures period '{temp_a}' while Document B reflects '{temp_b}'.",
                "context_difference": "temporal",
                "case_category": "case_3_contextual"
            }

        # Case 3: Contextual Reconciliation via Unit Difference
        if unit_a and unit_b and norm_unit_a != norm_unit_b:
            # Only reconcile if both units belong to the same physical dimension
            is_curr_a = any(c in norm_unit_a for c in ["crore", "million", "usd", "inr", "$", "₹"])
            is_curr_b = any(c in norm_unit_b for c in ["crore", "million", "usd", "inr", "$", "₹"])
            is_pct_a = any(p in norm_unit_a for p in ["%", "percent", "percentage", "bps"])
            is_pct_b = any(p in norm_unit_b for p in ["%", "percent", "percentage", "bps"])
            is_vol_a = any(v in norm_unit_a for v in ["kg", "ton", "units", "parcels", "employees"])
            is_vol_b = any(v in norm_unit_b for v in ["kg", "ton", "units", "parcels", "employees"])

            same_dimension = (is_curr_a and is_curr_b) or (is_pct_a and is_pct_b) or (is_vol_a and is_vol_b)
            if same_dimension:
                return {
                    "id": rel_id,
                    "fact_id_1": fa["id"],
                    "fact_id_2": fb["id"],
                    "doc_id_1": fa["document_id"],
                    "doc_id_2": fb["document_id"],
                    "relationship_type": "contextual_reconciliation",
                    "confidence": 0.90,
                    "reasoning": f"Apparent conflict is resolved by unit scale differences: Document A reports in {fa.get('unit', '')} whereas Document B reports in {fb.get('unit', '')}.",
                    "context_difference": "units",
                    "case_category": "case_3_contextual"
                }

        # Case 2: Genuine Contradiction (conflicting values for same subject, metric & scope)
        sub_a = str(fa.get("subject", "")).strip()
        sub_b = str(fb.get("subject", "")).strip()

        # Reject contradictions on generic subjects
        if sub_a in ["Quantitative Statement", "Reported Metric"] or sub_b in ["Quantitative Statement", "Reported Metric"]:
            return None

        # Dimensional unit check for contradiction: units must not be across incompatible dimensions
        if unit_a and unit_b:
            is_curr_a = any(c in norm_unit_a for c in ["crore", "million", "usd", "inr", "$", "₹"])
            is_curr_b = any(c in norm_unit_b for c in ["crore", "million", "usd", "inr", "$", "₹"])
            is_pct_a = any(p in norm_unit_a for p in ["%", "percent", "percentage", "bps"])
            is_pct_b = any(p in norm_unit_b for p in ["%", "percent", "percentage", "bps"])
            if (is_curr_a != is_curr_b) or (is_pct_a != is_pct_b):
                return None

        pred_a = str(fa.get("predicate", "")).lower().strip()
        pred_b = str(fb.get("predicate", "")).lower().strip()
        cat_a = str(fa.get("category", "")).lower().strip()
        cat_b = str(fb.get("category", "")).lower().strip()

        # Subject lexical overlap check
        tokens_sa = {w for w in re.findall(r'\b[a-z]{3,}\b', sub_a.lower()) if w not in STOP_WORDS}
        tokens_sb = {w for w in re.findall(r'\b[a-z]{3,}\b', sub_b.lower()) if w not in STOP_WORDS}
        subject_overlap = (len(tokens_sa.intersection(tokens_sb)) / len(tokens_sa.union(tokens_sb))) if (tokens_sa and tokens_sb) else 0.0

        if pred_a == "stated_value" and pred_b == "stated_value":
            predicates_compatible = (subject_overlap >= 0.40)
        else:
            predicates_compatible = (pred_a == pred_b) or \
                (any(w in pred_a for w in ["revenue", "sales"]) and any(w in pred_b for w in ["revenue", "sales"])) or \
                (any(w in pred_a for w in ["gdp", "growth"]) and any(w in pred_b for w in ["gdp", "growth"])) or \
                (subject_overlap >= 0.40)

        categories_compatible = (cat_a == cat_b) or cat_a == "quantitative" or cat_b == "quantitative"
        both_numeric = (num_a is not None and num_b is not None)
        both_text = (num_a is None and num_b is None and val_a and val_b)

        if val_a != val_b and predicates_compatible and categories_compatible and (both_numeric or both_text):
            if not temp_a or not temp_b or temp_a == temp_b:
                return {
                    "id": rel_id,
                    "fact_id_1": fa["id"],
                    "fact_id_2": fb["id"],
                    "doc_id_1": fa["document_id"],
                    "doc_id_2": fb["document_id"],
                    "relationship_type": "genuine_contradiction",
                    "confidence": 0.93,
                    "reasoning": f"Conflicting values reported for the same subject ({fa.get('subject')}) and metric under identical scope: Document A reports '{val_a} {fa.get('unit', '')}' while Document B reports '{val_b} {fb.get('unit', '')}'. This reflects genuine empirical or institutional forecast disagreement.",
                    "context_difference": "methodology",
                    "case_category": "case_2_contradiction"
                }

        return None
