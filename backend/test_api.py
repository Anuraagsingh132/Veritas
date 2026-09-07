import sys
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_endpoints():
    # 1. Root
    r = client.get("/")
    assert r.status_code == 200, f"Root failed: {r.status_code}"
    print("[OK] Root endpoint:", r.json()["name"])

    # 2. Documents
    r = client.get("/api/documents")
    assert r.status_code == 200
    docs = r.json()
    print(f"[OK] Documents endpoint: {len(docs)} documents found")

    # 3. Facts
    r = client.get("/api/facts")
    assert r.status_code == 200
    facts = r.json()
    print(f"[OK] Facts endpoint: {len(facts)} facts found")

    # 4. Reconciliation
    r = client.get("/api/reconciliation")
    assert r.status_code == 200
    rels = r.json()
    print(f"[OK] Reconciliation endpoint: {len(rels)} relationships found")

    # 5. Showcase (4 Required Cases)
    r = client.get("/api/showcase")
    assert r.status_code == 200
    cases = r.json()["cases"]
    print(f"[OK] Showcase endpoint: {len(cases)} cases found:")
    for c in cases:
        print(f"     * Case {c['case_number']}: {c['case_title']} ({c['case_type']})")

    # 6. System Stats
    r = client.get("/api/system/stats")
    assert r.status_code == 200
    stats = r.json()
    print("[OK] Stats endpoint:", stats)

if __name__ == "__main__":
    test_endpoints()
