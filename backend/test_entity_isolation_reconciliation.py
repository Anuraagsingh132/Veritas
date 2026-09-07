import unittest
from app.services.reconciler import FactReconciler

class TestEntityIsolationReconciliation(unittest.TestCase):
    """
    Unit test verifying that FactReconciler prevents false contradictions
    and false corroborations across different corporate entities.
    """

    def setUp(self):
        self.reconciler = FactReconciler(llm_client=None)

    def test_different_entities_do_not_contradict(self):
        # Apple vs Microsoft with different revenues
        fact_apple = {
            "id": "fact-apple-1",
            "document_id": "doc-apple",
            "entity": "Apple Inc.",
            "subject": "Apple Revenue",
            "predicate": "revenue",
            "value": "100",
            "unit": "USD Billion",
            "category": "financial",
            "temporal_context": "2024",
            "scope_context": "Consolidated"
        }
        fact_msft = {
            "id": "fact-msft-1",
            "document_id": "doc-msft",
            "entity": "Microsoft Corporation",
            "subject": "Microsoft Revenue",
            "predicate": "revenue",
            "value": "200",
            "unit": "USD Billion",
            "category": "financial",
            "temporal_context": "2024",
            "scope_context": "Consolidated"
        }

        rel = self.reconciler._heuristic_reconcile(fact_apple, fact_msft)
        self.assertIsNone(rel, "Different entities (Apple vs Microsoft) should NOT produce a contradiction!")
        print("[OK] test_different_entities_do_not_contradict PASSED: Apple vs Microsoft correctly returned None")

    def test_different_entities_do_not_corroborate(self):
        # Apple vs Microsoft with identical numbers
        fact_apple = {
            "id": "fact-apple-2",
            "document_id": "doc-apple",
            "entity": "Apple Inc.",
            "subject": "Apple Revenue",
            "predicate": "revenue",
            "value": "100",
            "unit": "USD Billion",
            "category": "financial",
            "temporal_context": "2024",
            "scope_context": "Consolidated"
        }
        fact_msft = {
            "id": "fact-msft-2",
            "document_id": "doc-msft",
            "entity": "Microsoft Corporation",
            "subject": "Microsoft Revenue",
            "predicate": "revenue",
            "value": "100",
            "unit": "USD Billion",
            "category": "financial",
            "temporal_context": "2024",
            "scope_context": "Consolidated"
        }

        rel = self.reconciler._heuristic_reconcile(fact_apple, fact_msft)
        self.assertIsNone(rel, "Different entities with identical numbers should NOT corroborate!")
        print("[OK] test_different_entities_do_not_corroborate PASSED: Identical numbers across different entities correctly returned None")

    def test_same_entity_corroboration_works(self):
        # Delhivery in two documents
        fact_d1 = {
            "id": "fact-delhivery-1",
            "document_id": "doc-delhivery-ar",
            "entity": "Delhivery Limited",
            "subject": "Delhivery Limited Revenue from Operations",
            "predicate": "revenue",
            "value": "81415.38",
            "unit": "INR Millions",
            "category": "financial",
            "temporal_context": "FY24",
            "scope_context": "Consolidated"
        }
        fact_d2 = {
            "id": "fact-delhivery-2",
            "document_id": "doc-delhivery-q4",
            "entity": "Delhivery Limited",
            "subject": "Delhivery Limited Revenue from Operations",
            "predicate": "revenue",
            "value": "8142",
            "unit": "INR Crores",
            "category": "financial",
            "temporal_context": "FY24",
            "scope_context": "Consolidated"
        }

        rel = self.reconciler._heuristic_reconcile(fact_d1, fact_d2)
        self.assertIsNotNone(rel, "Same entity with normalized matching values SHOULD corroborate!")
        self.assertEqual(rel["relationship_type"], "corroboration")
        print("[OK] test_same_entity_corroboration_works PASSED: Delhivery correctly corroborated across documents")

if __name__ == "__main__":
    unittest.main()
