from app.routers.showcase import get_four_required_cases

res = get_four_required_cases()
print(f"Retrieved {len(res.cases)} dynamic showcase cases from SQLite:")
for c in res.cases:
    print(f"\n[Case {c.case_number}] {c.case_title} ({c.case_type})")
    if c.fact_1:
        print(f"  Fact 1: [{c.fact_1.document_filename} p.{c.fact_1.page_number}] {c.fact_1.subject} = {c.fact_1.value} {c.fact_1.unit}")
        safe_q1 = c.fact_1.exact_quote[:80].encode('ascii', 'replace').decode('ascii')
        print(f"  Quote 1: \"{safe_q1}...\"")
        print(f"  Bbox 1: {c.fact_1.bbox}")
    if c.fact_2:
        print(f"  Fact 2: [{c.fact_2.document_filename} p.{c.fact_2.page_number}] {c.fact_2.subject} = {c.fact_2.value} {c.fact_2.unit}")
        safe_q2 = c.fact_2.exact_quote[:80].encode('ascii', 'replace').decode('ascii')
        print(f"  Quote 2: \"{safe_q2}...\"")
        print(f"  Bbox 2: {c.fact_2.bbox}")
    safe_reasoning = c.reasoning[:120].encode('ascii', 'replace').decode('ascii')
    print(f"  Reasoning: {safe_reasoning}...")
    if c.resolution_or_mitigation:
        safe_mit = c.resolution_or_mitigation[:100].encode('ascii', 'replace').decode('ascii')
        print(f"  Mitigation: {safe_mit}...")
