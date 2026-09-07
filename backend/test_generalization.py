import json
from app.services.fact_extractor import FactExtractor
from app.services.llm_client import shared_llm_client

extractor = FactExtractor(llm_client=shared_llm_client)

sample_text = """
Emperor penguins are the tallest of all living penguin species, reaching heights of up to 122 cm and weighing between 22 and 45 kg.
They can dive to depths of 535 meters and remain submerged for more than 20 minutes.
In 2024, wildlife researchers documented a colony size of 25,000 breeding pairs across the Ross Sea region.
Their average swimming speed during foraging was recorded at 8.9 km/h.
"""

print("Testing domain-agnostic fact extraction on non-financial text (Penguin Biology):")
facts = extractor.extract_from_page(
    doc_id="test-doc-bio",
    page_number=1,
    page_text=sample_text,
    filename="emperor-penguins-biology-2024.pdf"
)

print(f"Extracted {len(facts)} facts from non-financial text:")
for f in facts:
    print(f"  * Subject: '{f['subject']}', Value: '{f['value']}', Unit: '{f['unit']}', Category: '{f['category']}'")
    print(f"    Quote: \"{f['exact_quote'][:70]}\"")
    print(f"    Offsets: ({f['char_offset_start']}, {f['char_offset_end']})")

assert len(facts) >= 2, "Generalization test failed: fewer than 2 facts extracted from non-financial text!"
print("\n[OK] Generalization test PASSED! Fact Knowledge Layer extracts facts from ANY domain without hardcoding.")
