import sys
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_endpoints():
    # 1. API Info
    r = client.get("/api/info")
    assert r.status_code == 200, f"API Info failed: {r.status_code}"
    print("[OK] API Info endpoint:", r.json()["name"])

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
    if facts:
        first_id = facts[0]["id"]
        r_single = client.get(f"/api/facts/{first_id}")
        assert r_single.status_code == 200
        print(f"[OK] Single Fact detail endpoint for {first_id}: retrieved with {len(r_single.json()['relationships'])} relationships")

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
