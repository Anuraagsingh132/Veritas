import unittest
from app.services.fact_extractor import FactExtractor

class TestSlideNewlineExtraction(unittest.TestCase):
    """
    Unit test verifying that presentation slides lacking periods are NOT dropped
    by the heuristic extractor, and that dense slide text splits across newlines
    and extracts metrics like revenue and EBITDA.
    """

    def setUp(self):
        self.extractor = FactExtractor(llm_client=None)

    def test_presentation_slide_without_periods_extracts_metrics(self):
        # Sample dense text from an investor presentation slide without periods
        slide_text = (
            "FY24 Financial & Operational Highlights\n"
            "₹8,142 Cr\n"
            "FY24 revenue from services\n"
            "YoY: 12.7%\n"
            "₹263 Cr\n"
            "Adjusted EBITDA\n"
            "Margin: 3.2%\n"
            "Express Parcel shipment volume\n"
            "743 Mn parcels delivered globally in FY24\n"
            "Active customer base grew to 30,500 clients"
        )

        facts = self.extractor._heuristic_extract(
            doc_id="test-slide-doc",
            page_number=6,
            page_text=slide_text,
            blocks=[],
            filename="delhivery_presentation.pdf"
        )

        self.assertTrue(len(facts) >= 2, f"Expected at least 2 facts extracted from slide, got {len(facts)}")

        values = [f["value"] for f in facts]
        print(f"[OK] Extracted values from slide without periods: {values}")
        
        # Verify 8142 is among extracted values
        self.assertIn("8142", values, "Failed to extract key revenue metric '8142' from slide!")
        print("[OK] test_presentation_slide_without_periods_extracts_metrics PASSED.")

if __name__ == "__main__":
    unittest.main()
