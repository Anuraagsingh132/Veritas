import unittest
from app.services.reconciler import FactReconciler

class TestIncompatibleUnitsDoNotReconcile(unittest.TestCase):
    """
    Unit test verifying that FactReconciler prevents dimensional mismatch reconciliations.
    Specifically, a financial currency amount (e.g. INR Crores) and a percentage (e.g. %)
    or physical volume (e.g. kg) must NEVER be reconciled as 'unit differences'.
    """

    def setUp(self):
        self.reconciler = FactReconciler(llm_client=None)

    def test_currency_vs_percentage_does_not_reconcile(self):
        fact_curr = {
            "id": "fact-curr-1",
            "document_id": "doc-a",
            "entity": "Delhivery Limited",
            "subject": "Delhivery Revenue",
            "predicate": "revenue",
            "value": "8142",
            "unit": "INR Crores",
            "category": "financial",
            "temporal_context": "FY24",
            "scope_context": "Consolidated"
        }
        fact_pct = {
            "id": "fact-pct-1",
            "document_id": "doc-b",
            "entity": "Delhivery Limited",
            "subject": "Delhivery Growth Rate",
            "predicate": "revenue",
            "value": "12.7",
            "unit": "%",
            "category": "financial",
            "temporal_context": "FY24",
            "scope_context": "Consolidated"
        }

        rel = self.reconciler._heuristic_reconcile(fact_curr, fact_pct)
        self.assertIsNone(
            rel,
            "Incompatible dimensions (Currency vs Percentage) should NEVER be classified as contextual reconciliation!"
        )
        print("[OK] test_currency_vs_percentage_does_not_reconcile PASSED: returned None.")

    def test_same_dimension_unit_reconciliation_works(self):
        # USD vs INR or Crore vs Million is acceptable
        fact_m = {
            "id": "fact-m-1",
            "document_id": "doc-a",
            "entity": "Delhivery Limited",
            "subject": "Delhivery Revenue",
            "predicate": "revenue",
            "value": "81415.38",
            "unit": "INR Millions",
            "category": "financial",
            "temporal_context": "FY24",
            "scope_context": "Consolidated"
        }
        fact_cr = {
            "id": "fact-cr-1",
            "document_id": "doc-b",
            "entity": "Delhivery Limited",
            "subject": "Delhivery Revenue",
            "predicate": "revenue",
            "value": "8142",
            "unit": "INR Crores",
            "category": "financial",
            "temporal_context": "FY24",
            "scope_context": "Consolidated"
        }

        rel = self.reconciler._heuristic_reconcile(fact_m, fact_cr)
        self.assertIsNotNone(rel)
        self.assertEqual(rel["relationship_type"], "corroboration")
        print("[OK] test_same_dimension_unit_reconciliation_works PASSED: corroborated across same dimension.")

if __name__ == "__main__":
    unittest.main()
