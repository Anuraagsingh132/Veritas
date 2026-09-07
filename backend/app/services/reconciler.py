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

Format your response as a JSON object:
{
  "relationship_type": "corroboration | genuine_contradiction | contextual_reconciliation | extraction_failure",
  "confidence": 0.95,
  "case_category": "case_1_corroboration | case_2_contradiction | case_3_contextual | case_4_failure",
  "context_difference": "temporal | scope | units | methodology | none",
  "reasoning": "Clear, rigorous multi-sentence explanation of why these two facts corroborate, contradict, or reconcile."
}
"""

STOP_WORDS = {
    "the", "and", "of", "in", "to", "for", "a", "an", "is", "was", "by", "on", "at",
    "from", "as", "with", "that", "this", "it", "are", "were", "be", "or", "total"
}

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

                pair_key = tuple(sorted([fa["id"], fb["id"]]))
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                score = self._compute_similarity(fa, fb)
                if score > 0.15:  # Sufficient semantic overlap
                    first, second = (fa, fb) if fa["id"] < fb["id"] else (fb, fa)
                    scored_pairs.append((score, first, second))

        # Sort by similarity score descending and cap at max_candidates
        scored_pairs.sort(key=lambda x: x[0], reverse=True)
        return [(fa, fb) for _, fa, fb in scored_pairs[:self.max_candidates]]

    def _compute_similarity(self, fa: Dict[str, Any], fb: Dict[str, Any]) -> float:
        """
        Calculates token Jaccard similarity between two facts across subject, predicate, and quotes.
        """
        text_a = f"{fa.get('subject', '')} {fa.get('predicate', '')} {fa.get('category', '')}".lower()
        text_b = f"{fb.get('subject', '')} {fb.get('predicate', '')} {fb.get('category', '')}".lower()

        tokens_a = {w for w in re.findall(r'\b[a-z]{3,}\b', text_a) if w not in STOP_WORDS}
        tokens_b = {w for w in re.findall(r'\b[a-z]{3,}\b', text_b) if w not in STOP_WORDS}

        if not tokens_a or not tokens_b:
            return 0.0

        intersection = len(tokens_a.intersection(tokens_b))
        union = len(tokens_a.union(tokens_b))
        jaccard = intersection / union if union > 0 else 0.0

        # Category bonus
        if fa.get("category") == fb.get("category") and fa.get("category"):
            jaccard += 0.2

        # Temporal match bonus
        if fa.get("temporal_context") and fa.get("temporal_context") == fb.get("temporal_context"):
            jaccard += 0.25

        return jaccard

    def _compare_pair_llm(self, fa: Dict[str, Any], fb: Dict[str, Any]) -> Dict[str, Any]:
        """Classifies relationship using LLM."""
        if fa["id"] > fb["id"]:
            fa, fb = fb, fa

        rel_id = self.generate_relationship_id(fa["id"], fb["id"])

        prompt = (
            f"Fact 1 (from doc {fa.get('document_id')}):\n"
            f"Subject: {fa.get('subject')}\n"
            f"Predicate: {fa.get('predicate')}\n"
            f"Value: {fa.get('value')} {fa.get('unit', '')}\n"
            f"Temporal: {fa.get('temporal_context')}\n"
            f"Scope: {fa.get('scope_context')}\n"
            f"Quote: \"{fa.get('exact_quote')}\"\n\n"
            f"Fact 2 (from doc {fb.get('document_id')}):\n"
            f"Subject: {fb.get('subject')}\n"
            f"Predicate: {fb.get('predicate')}\n"
            f"Value: {fb.get('value')} {fb.get('unit', '')}\n"
            f"Temporal: {fb.get('temporal_context')}\n"
            f"Scope: {fb.get('scope_context')}\n"
            f"Quote: \"{fb.get('exact_quote')}\""
        )
        res = self.llm.chat_json(RECONCILIATION_SYSTEM_PROMPT, prompt)
        
        return {
            "id": rel_id,
            "fact_id_1": fa["id"],
            "fact_id_2": fb["id"],
            "doc_id_1": fa["document_id"],
            "doc_id_2": fb["document_id"],
            "relationship_type": res.get("relationship_type", "contextual_reconciliation"),
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
                return self._compare_pair_llm(fa, fb)
            except Exception as e:
                logger.warning(f"LLM reconciliation call failed: {e}. Falling back to rule-based reconciliation.")

        return self._heuristic_reconcile(fa, fb)

    def _heuristic_reconcile(self, fa: Dict[str, Any], fb: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Rigorous, domain-agnostic epistemological rules that work across any topic:
        - Exact numeric/semantic match -> Corroboration
        - Differing values + distinct time periods/units/scopes -> Contextual Reconciliation
        - Conflicting values + identical time period & scope -> Genuine Contradiction
        """
        if fa["id"] > fb["id"]:
            fa, fb = fb, fa

        rel_id = self.generate_relationship_id(fa["id"], fb["id"])

        val_a = str(fa.get("value", "")).strip().replace(",", "")
        val_b = str(fb.get("value", "")).strip().replace(",", "")
        temp_a = str(fa.get("temporal_context", "")).strip().lower()
        temp_b = str(fb.get("temporal_context", "")).strip().lower()
        unit_a = str(fa.get("unit", "")).strip().lower()
        unit_b = str(fb.get("unit", "")).strip().lower()
        scope_a = str(fa.get("scope_context", "")).strip().lower()
        scope_b = str(fb.get("scope_context", "")).strip().lower()

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

        # Case 1: Corroboration (exact value equality, or numeric difference <= 1% due to rounding)
        try:
            num_a = float(val_a)
            num_b = float(val_b)
            if abs(num_a - num_b) < 1e-5 or (max(num_a, num_b) > 0 and abs(num_a - num_b) / max(num_a, num_b) < 0.01):
                return {
                    "id": rel_id,
                    "fact_id_1": fa["id"],
                    "fact_id_2": fb["id"],
                    "doc_id_1": fa["document_id"],
                    "doc_id_2": fb["document_id"],
                    "relationship_type": "corroboration",
                    "confidence": 0.95,
                    "reasoning": f"Both documents independently affirm the value of {fa.get('subject')} at approximately '{val_a}', confirming ground truth across independent publications.",
                    "context_difference": "none",
                    "case_category": "case_1_corroboration"
                }
        except (ValueError, TypeError):
            if val_a and val_a == val_b:
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

        # Case 3: Contextual Reconciliation via Unit / Scope Difference
        if (unit_a and unit_b and unit_a != unit_b) or (scope_a and scope_b and scope_a != scope_b):
            dim = "units" if (unit_a != unit_b) else "scope"
            return {
                "id": rel_id,
                "fact_id_1": fa["id"],
                "fact_id_2": fb["id"],
                "doc_id_1": fa["document_id"],
                "doc_id_2": fb["document_id"],
                "relationship_type": "contextual_reconciliation",
                "confidence": 0.90,
                "reasoning": f"Apparent conflict is resolved by differences in reporting {dim}: Document A reports {fa.get('scope_context', '')} in {fa.get('unit', '')} whereas Document B reports {fb.get('scope_context', '')} in {fb.get('unit', '')}.",
                "context_difference": dim,
                "case_category": "case_3_contextual"
            }

        # Case 2: Genuine Contradiction (conflicting values for same temporal period and scope)
        if val_a != val_b and (not temp_a or not temp_b or temp_a == temp_b):
            return {
                "id": rel_id,
                "fact_id_1": fa["id"],
                "fact_id_2": fb["id"],
                "doc_id_1": fa["document_id"],
                "doc_id_2": fb["document_id"],
                "relationship_type": "genuine_contradiction",
                "confidence": 0.93,
                "reasoning": f"Conflicting values reported for the same subject ({fa.get('subject')}) under identical scope: Document A reports '{val_a}' while Document B reports '{val_b}'. This reflects genuine empirical or methodological disagreement.",
                "context_difference": "methodology",
                "case_category": "case_2_contradiction"
            }

        return None
