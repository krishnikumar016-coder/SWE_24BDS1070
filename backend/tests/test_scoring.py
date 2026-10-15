import pytest
from app.core.scoring import compute_cbi_scores, score_item

def test_score_item_reverse():
    # FREQ scale reverse (W7)
    # Always -> 0 (instead of 100)
    # Often -> 25 (instead of 75)
    # Sometimes -> 50 (instead of 50)
    # Seldom -> 75 (instead of 25)
    # Never/almost never -> 100 (instead of 0)
    assert score_item("FREQ", "Always", reverse=True) == 0.0
    assert score_item("FREQ", "Often", reverse=True) == 25.0
    assert score_item("FREQ", "Sometimes", reverse=True) == 50.0
    assert score_item("FREQ", "Seldom", reverse=True) == 75.0
    assert score_item("FREQ", "Never/almost never", reverse=True) == 100.0

def test_cbi_full_scoring():
    answers = {
        # Personal (all Often = 75)
        "P1": "Often", "P2": "Often", "P3": "Often", "P4": "Often", "P5": "Often", "P6": "Often",
        # Work (all Sometimes = 50, W7 Always -> reversed 0)
        "W1": "Somewhat", "W2": "Somewhat", "W3": "Somewhat", "W4": "Sometimes", "W5": "Sometimes", "W6": "Sometimes", "W7": "Always",
        # Client (all Seldom / To a low degree = 25)
        "C1": "To a low degree", "C2": "To a low degree", "C3": "To a low degree", "C4": "To a low degree", "C5": "Seldom", "C6": "Seldom",
        # Supplementary
        "S1": "Somewhat", "S2": "Often", "S3": "Often", "S4": "Often", "S5": "Often"
    }

    res = compute_cbi_scores(answers, client_contact_role=True)
    assert res["personal_score"] == 75.0
    # Work score: (50*6 + 0) / 7 = 300 / 7 = 42.86
    assert res["work_score"] == 42.86
    assert res["client_score"] == 25.0
    # Composite score: mean(75.0, 42.86, 25.0) = 142.86 / 3 = 47.62
    assert res["composite_score"] == 47.62
    # 47.62 is between 35 and 50 -> Moderate
    assert res["risk_category"] == "Moderate"

def test_non_responder_rule():
    # Only 2 Personal items answered (threshold is 3)
    # Only 3 Work items answered (threshold is 4)
    # 3 Client items answered (threshold is 3)
    partial_answers = {
        "P1": "Often", "P2": "Often",
        "W1": "Somewhat", "W2": "Somewhat", "W3": "Somewhat",
        "C1": "To a high degree", "C2": "To a high degree", "C3": "To a high degree"
    }
    res = compute_cbi_scores(partial_answers, client_contact_role=True)
    assert res["personal_score"] is None  # < 3 answered
    assert res["work_score"] is None      # < 4 answered
    assert res["client_score"] == 75.0    # 3 answered >= 3

    # Composite should be equal to the active subscale (Client = 75.0) -> High
    assert res["composite_score"] == 75.0
    assert res["risk_category"] == "High"

def test_optional_client_subscale_disabled():
    answers = {
        "P1": "Always", "P2": "Always", "P3": "Always", "P4": "Always", "P5": "Always", "P6": "Always",
        "W1": "To a very high degree", "W2": "To a very high degree", "W3": "To a very high degree",
        "W4": "Always", "W5": "Always", "W6": "Always", "W7": "Never/almost never", # W7 reversed -> 100
        "C1": "To a low degree", "C2": "To a low degree", "C3": "To a low degree"
    }
    # Disabled client contact role
    res = compute_cbi_scores(answers, client_contact_role=False)
    assert res["personal_score"] == 100.0
    assert res["work_score"] == 100.0
    assert res["client_score"] is None
    assert res["composite_score"] == 100.0
    assert res["risk_category"] == "High"
