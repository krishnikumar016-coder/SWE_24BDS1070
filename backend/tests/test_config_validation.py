import pytest
from app.core.scoring import CBI_CONFIG

def test_cbi_config_structure():
    """
    Validates that the CBI JSON config adheres strictly to Copenhagen Burnout Inventory (2004) spec:
    - 19 items total: 6 Personal, 7 Work, 6 Client.
    - Scales: FREQ and INTENSITY.
    - Reverse scoring: ONLY W7.
    - Non-responder thresholds: Personal 3, Work 4, Client 3.
    - Client subscale marked optional.
    """
    subscales = CBI_CONFIG["subscales"]
    
    # 1. Personal Subscale Check
    personal = subscales["personal"]
    assert len(personal["items"]) == 6, f"Expected 6 Personal items, got {len(personal['items'])}"
    assert personal["min_responses_required"] == 3
    for item in personal["items"]:
        assert item["scale"] == "FREQ"
        assert item["reverse"] is False, f"Personal item {item['id']} should not be reversed"
    personal_ids = [item["id"] for item in personal["items"]]
    assert personal_ids == ["P1", "P2", "P3", "P4", "P5", "P6"]

    # 2. Work-related Subscale Check
    work = subscales["work"]
    assert len(work["items"]) == 7, f"Expected 7 Work items, got {len(work['items'])}"
    assert work["min_responses_required"] == 4
    work_ids = [item["id"] for item in work["items"]]
    assert work_ids == ["W1", "W2", "W3", "W4", "W5", "W6", "W7"]
    
    # Check W1..W3 are INTENSITY, W4..W7 are FREQ
    for item in work["items"]:
        if item["id"] in ["W1", "W2", "W3"]:
            assert item["scale"] == "INTENSITY"
        else:
            assert item["scale"] == "FREQ"
        
        # Only W7 should be reversed
        if item["id"] == "W7":
            assert item["reverse"] is True, "W7 MUST be reverse-scored"
        else:
            assert item["reverse"] is False, f"{item['id']} should not be reverse-scored"

    # 3. Client-related Subscale Check
    client = subscales["client"]
    assert len(client["items"]) == 6, f"Expected 6 Client items, got {len(client['items'])}"
    assert client["min_responses_required"] == 3
    assert client.get("optional") is True, "Client subscale must be optional"
    client_ids = [item["id"] for item in client["items"]]
    assert client_ids == ["C1", "C2", "C3", "C4", "C5", "C6"]
    
    for item in client["items"]:
        if item["id"] in ["C1", "C2", "C3", "C4"]:
            assert item["scale"] == "INTENSITY"
        else:
            assert item["scale"] == "FREQ"
        assert item["reverse"] is False, f"Client item {item['id']} should not be reversed"

    # 4. Supplementary items check
    supp = CBI_CONFIG["supplementary_items"]
    assert len(supp) >= 4, "Must have 4-6 supplementary items"
    for item in supp:
        assert item["id"].startswith("S")

    # 5. Cutoffs check
    cutoffs = CBI_CONFIG["cutoffs"]
    assert cutoffs["low_moderate_boundary"] == 35.0
    assert cutoffs["high_boundary"] == 50.0
