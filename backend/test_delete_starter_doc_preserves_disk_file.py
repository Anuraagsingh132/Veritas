import unittest
import uuid
from pathlib import Path
from fastapi.testclient import TestClient
from main import app
from app.db import get_db_connection
from app.config import settings

class TestDeleteDocumentFilePreservation(unittest.TestCase):
    """
    Test suite verifying that DELETE /api/documents/{id} does not delete
    files outside of the uploads directory (such as starter-datasets).
    """

    def setUp(self):
        self.client = TestClient(app)
        self.conn = get_db_connection()

    def tearDown(self):
        self.conn.close()

    def test_delete_starter_doc_preserves_disk_file(self):
        # Locate an actual starter dataset file
        starter_file = Path(__file__).resolve().parent.parent / "starter-datasets" / "delhivery" / "03-delhivery-q4-fy24-earnings-presentation.pdf"
        self.assertTrue(starter_file.exists(), f"Starter file does not exist: {starter_file}")

        # Insert a dummy document referencing this starter file
        test_doc_id = f"test-starter-{uuid.uuid4().hex[:6]}"
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO documents (id, filename, filepath, filesize, page_count, dataset_tag, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (test_doc_id, starter_file.name, str(starter_file), 12345, 10, "starter-test", "completed")
        )
        self.conn.commit()

        # Delete document via API
        response = self.client.delete(f"/api/documents/{test_doc_id}")
        self.assertEqual(response.status_code, 200, f"Delete failed: {response.text}")

        # Verify record was deleted from database
        cursor.execute("SELECT id FROM documents WHERE id = ?", (test_doc_id,))
        self.assertIsNone(cursor.fetchone(), "Document was not removed from DB")

        # Crucial: Verify starter file on disk was PRESERVED
        self.assertTrue(starter_file.exists(), "CRITICAL BUG: Starter dataset file was deleted from disk!")
        print("[OK] test_delete_starter_doc_preserves_disk_file PASSED: Starter file preserved on disk.")

    def test_delete_uploaded_doc_cleans_up_upload_dir(self):
        # Create a temp file in uploads
        temp_upload = settings.UPLOAD_DIR / f"test_temp_{uuid.uuid4().hex[:6]}.pdf"
        temp_upload.write_bytes(b"%PDF-1.4 dummy content")
        self.assertTrue(temp_upload.exists())

        test_doc_id = f"test-upload-{uuid.uuid4().hex[:6]}"
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO documents (id, filename, filepath, filesize, page_count, dataset_tag, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (test_doc_id, temp_upload.name, str(temp_upload), 100, 1, "upload-test", "completed")
        )
        self.conn.commit()

        # Delete document via API
        response = self.client.delete(f"/api/documents/{test_doc_id}")
        self.assertEqual(response.status_code, 200)

        # Verify DB deletion
        cursor.execute("SELECT id FROM documents WHERE id = ?", (test_doc_id,))
        self.assertIsNone(cursor.fetchone())

        # Verify upload file was cleaned up from disk
        self.assertFalse(temp_upload.exists(), "Uploaded file in uploads/ was not unlinked.")
        print("[OK] test_delete_uploaded_doc_cleans_up_upload_dir PASSED: Uploaded file cleaned up correctly.")

if __name__ == "__main__":
    unittest.main()
