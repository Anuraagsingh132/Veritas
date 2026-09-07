import unittest
from unittest.mock import MagicMock
from app.services.fact_extractor import FactExtractor
from app.services.llm_client import LLMClient

class TestStrictEvidenceGrounding(unittest.TestCase):
    """
    Unit test suite verifying that FactExtractor strictly enforces evidence grounding
    and rejects LLM hallucinations that cannot be verified in the source PDF text.
    """

    def setUp(self):
        self.mock_llm = MagicMock(spec=LLMClient)
        self.mock_llm.is_available.return_value = True
        self.extractor = FactExtractor(llm_client=self.mock_llm)

    def test_rejects_hallucinated_quote(self):
        page_text = (
            "The company reported consolidated revenue of 5,000 Crores in FY24, "
            "representing an annual growth rate of 12 percent over the previous year."
        )

        # Mock LLM returning one grounded fact and one fabricated fact with a hallucinated quote
        self.mock_llm.chat_json.return_value = {
            "facts": [
                {
                    "category": "financial",
                    "subject": "Consolidated Revenue",
                    "predicate": "reported_value",
                    "value": "5000",
                    "unit": "Crores",
                    "temporal_context": "FY24",
                    "exact_quote": "consolidated revenue of 5,000 Crores in FY24",  # VERIFIED IN TEXT
                    "confidence": 0.95
                },
                {
                    "category": "financial",
                    "subject": "EBITDA Margin",
                    "predicate": "reported_margin",
                    "value": "25",
                    "unit": "%",
                    "temporal_context": "FY24",
                    "exact_quote": "EBITDA margin reached an unprecedented 25 percent across all business units",  # HALLUCINATED
                    "confidence": 0.90
                }
            ]
        }

        extracted = self.extractor.extract_from_page(
            doc_id="test-doc-1",
            page_number=1,
            page_text=page_text,
            filename="sample-filing.pdf"
        )

        # Assert that only the verified fact was accepted
        self.assertEqual(len(extracted), 1, "Expected exactly 1 grounded fact; hallucinated fact was not dropped!")
        self.assertEqual(extracted[0]["subject"], "Consolidated Revenue")
        self.assertIn("consolidated revenue of 5,000 Crores in FY24", extracted[0]["exact_quote"])
        print("[OK] test_rejects_hallucinated_quote PASSED: Successfully dropped hallucinated quote!")

if __name__ == "__main__":
    unittest.main()
