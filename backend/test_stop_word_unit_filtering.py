import unittest
from app.services.fact_extractor import FactExtractor

class TestStopWordUnitFiltering(unittest.TestCase):
    """
    Test suite verifying that FactExtractor._heuristic_extract strips stop-words
    (e.g., 'was', 'were', 'and', 'the', 'of', 'in') from unit strings,
    and correctly ignores fiscal year/quarter prefixes like FY24 and Q3.
    """

    def setUp(self):
        self.extractor = FactExtractor(llm_client=None)

    def test_stop_words_stripped_from_units(self):
        # Sample sentence where words like 'was' or 'and' might follow numbers
        text = (
            "In FY24 revenue was ₹8,142 Cr across all operations. "
            "Total headcount in 2024 was 30,000 employees globally. "
            "The volume grew by 15% during the fourth quarter."
        )

        facts = self.extractor._heuristic_extract(
            doc_id="test-doc-1",
            page_number=1,
            page_text=text,
            blocks=[],
            filename="delhivery_report.pdf"
        )
        self.assertTrue(len(facts) > 0, "Should have extracted at least one fact")

        INVALID_UNITS = {
            "was", "were", "is", "are", "the", "of", "in", "to", "for", "and", "a", "an",
            "at", "by", "from", "on", "with", "as", "or", "than", "over", "under", "per"
        }

        for fact in facts:
            unit = fact.get("unit", "").lower().strip()
            # Verify unit is not a bare stop word
            self.assertNotIn(unit, INVALID_UNITS, f"Extracted fact has invalid stop-word unit: '{unit}' in fact: {fact}")
            # Verify unit does not match raw prefix
            self.assertFalse(unit.startswith("fy"), f"Extracted fact unit starts with fiscal year: '{unit}'")
            print(f"[OK] Extracted fact: subject='{fact['subject']}', value='{fact['value']}', unit='{fact['unit']}', entity='{fact['entity']}'")

    def test_fiscal_year_prefixes_not_treated_as_fact_values(self):
        text = "During FY24 the company achieved record performance with EBITDA of ₹263 Cr in Q3."
        facts = self.extractor._heuristic_extract(
            doc_id="test-doc-2",
            page_number=1,
            page_text=text,
            blocks=[],
            filename="delhivery.pdf"
        )

        for fact in facts:
            # FY24 or Q3 should not be extracted as value '24' or '3'
            self.assertNotIn(fact["value"], ["24", "3"], f"Fiscal year or quarter number extracted as standalone value: {fact}")

        print("[OK] test_fiscal_year_prefixes_not_treated_as_fact_values PASSED")

if __name__ == "__main__":
    unittest.main()
