import unittest
import io
from fastapi.testclient import TestClient
from main import app

class TestUploadZeroBytePdf(unittest.TestCase):
    """
    Test suite verifying that uploading a 0-byte (empty) PDF returns HTTP 400
    with a clear error message and does not crash or corrupt the pipeline.
    """

    def setUp(self):
        self.client = TestClient(app)

    def test_upload_zero_byte_pdf_rejected(self):
        # Create an empty in-memory byte buffer
        empty_pdf = io.BytesIO(b"")
        files = {
            "file": ("empty.pdf", empty_pdf, "application/pdf")
        }
        
        response = self.client.post("/api/documents/upload", files=files)
        
        self.assertEqual(response.status_code, 400, f"Expected 400, got {response.status_code}: {response.text}")
        json_data = response.json()
        self.assertIn("detail", json_data)
        self.assertIn("empty (0-byte) PDF", json_data["detail"])
        print("[OK] test_upload_zero_byte_pdf_rejected PASSED: HTTP 400 received with expected detail.")

if __name__ == "__main__":
    unittest.main()
