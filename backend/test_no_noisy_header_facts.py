import unittest
from app.services.fact_extractor import FactExtractor

class TestNoNoisyHeaderFacts(unittest.TestCase):
    """
    Test suite verifying that document headers, footers, and page numbers
    (e.g., '9 Annual Report 2023-24') are NOT parsed as financial facts,
    and that 'Quantitative Statement' is not created for bare page numbers.
    """

    def setUp(self):
        self.extractor = FactExtractor(llm_client=None)

    def test_header_page_numbers_discarded(self):
        # Sample header text from annual reports that previously produced 'Quantitative Statement = 9 Annual'
        header_text = (
            "9\n"
            "Annual Report 2023-24\n"
            "Corporate Overview\n"
            "Statutory Reports\n"
            "Financial Statements"
        )

        facts = self.extractor._heuristic_extract(
            doc_id="test-header-doc",
            page_number=5,
            page_text=header_text,
            blocks=[],
            filename="02-delhivery-annual-report-fy24-excerpt.pdf"
        )

        # Verify that page number 9 is NOT extracted as a fact
        values = [f["value"] for f in facts]
        self.assertNotIn("9", values, f"Page number 9 was incorrectly extracted as a fact: {facts}")

        # Verify no fact has subject 'Quantitative Statement' with unit 'Annual'
        for f in facts:
            self.assertNotEqual(f.get("unit", "").lower(), "annual")
            if f.get("subject") == "Quantitative Statement":
                self.assertFalse(f["value"].isdigit() and int(f["value"]) < 250)

        print("[OK] test_header_page_numbers_discarded PASSED: No header page numbers extracted.")

    def test_footer_definitions_section_discarded(self):
        footer_text = "SECTION 4 - DEFINITIONS\nPage 88 of Annual Report"
        facts = self.extractor._heuristic_extract(
            doc_id="test-footer-doc",
            page_number=88,
            page_text=footer_text,
            blocks=[],
            filename="report.pdf"
        )

        values = [f["value"] for f in facts]
        self.assertNotIn("88", values)
        print("[OK] test_footer_definitions_section_discarded PASSED: No footer numbers extracted.")

if __name__ == "__main__":
    unittest.main()
