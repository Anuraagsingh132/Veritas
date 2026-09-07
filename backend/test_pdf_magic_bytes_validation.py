import unittest
import io
from fastapi.testclient import TestClient
from main import app

class TestPdfMagicBytesValidation(unittest.TestCase):
    """
    Test suite verifying that POST /api/documents/upload validates the PDF
    file signature (%PDF-) and rejects non-PDF files even if they have a .pdf extension.
    """

    def setUp(self):
        self.client = TestClient(app)

    def test_non_pdf_file_with_pdf_extension_rejected(self):
        # Fake PDF: binary executable or arbitrary text disguised with .pdf extension
        fake_content = io.BytesIO(b"This is just plain text, not a real PDF document.")
        files = {
            "file": ("fake_document.pdf", fake_content, "application/pdf")
        }

        response = self.client.post("/api/documents/upload", files=files)
        self.assertEqual(response.status_code, 400, f"Expected 400, got {response.status_code}: {response.text}")
        data = response.json()
        self.assertIn("detail", data)
        self.assertIn("%PDF- signature", data["detail"])
        print("[OK] test_non_pdf_file_with_pdf_extension_rejected PASSED: Rejected with HTTP 400.")

    def test_valid_pdf_signature_accepted(self):
        # Minimal valid PDF header
        valid_pdf_content = io.BytesIO(b"%PDF-1.4\n%Minimal valid test PDF\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF")
        files = {
            "file": ("valid_test.pdf", valid_pdf_content, "application/pdf")
        }

        response = self.client.post("/api/documents/upload", files=files)
        self.assertEqual(response.status_code, 200, f"Expected 200, got {response.status_code}: {response.text}")
        data = response.json()
        self.assertEqual(data["status"], "processing")
        print("[OK] test_valid_pdf_signature_accepted PASSED: Valid PDF accepted for processing.")

if __name__ == "__main__":
    unittest.main()
