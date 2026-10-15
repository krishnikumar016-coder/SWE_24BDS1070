import datetime
import pytest
from app.core.early_warning import evaluate_early_warning_triggers

def test_trigger_a_prob_rise():
    # Baseline prob ~ 0.15, predicted prob = 0.40 (rise = 0.25 > 0.15)
    res = evaluate_early_warning_triggers(
        current_composite=30.0,
        predicted_next_high_prob=0.40,
        user_history_composites=[25.0, 28.0]
    )
    assert res["alert_triggered"] is True
    assert any("Trigger A" in t for t in res["triggers"])
    assert res["severity"] in ["Watch", "Warning"]

def test_trigger_b_score_rise_10():
    # Composite rose by 12 points across last 2 assessments
    res = evaluate_early_warning_triggers(
        current_composite=42.0,
        predicted_next_high_prob=0.30,
        user_history_composites=[30.0]
    )
    assert res["alert_triggered"] is True
    assert any("Trigger B" in t for t in res["triggers"])
    assert res["severity"] == "Warning"

def test_trigger_c_sustained_high():
    # 3 consecutive assessments >= 35
    res = evaluate_early_warning_triggers(
        current_composite=55.0,
        predicted_next_high_prob=0.60,
        user_history_composites=[38.0, 42.0]
    )
    assert res["alert_triggered"] is True
    assert any("Trigger C" in t for t in res["triggers"])
    assert res["severity"] == "Urgent"
    assert res["supportive_message"] is not None
    assert "confidential self-support aid" in res["supportive_message"]

def test_cooldown_deduplication():
    now = datetime.datetime.utcnow()
    last_alert_time = now - datetime.timedelta(days=5)  # 5 days ago (within 14-day cooldown)
    
    # Moderate risk (Warning severity) should be suppressed by cooldown
    res = evaluate_early_warning_triggers(
        current_composite=40.0,
        predicted_next_high_prob=0.30,
        user_history_composites=[25.0],  # Trigger B (+15 rise)
        last_alert_timestamp=last_alert_time,
        cooldown_days=14
    )
    assert res["alert_triggered"] is False
    assert "cooldown" in res["reason"]

    # Urgent severity overrides cooldown
    res_urgent = evaluate_early_warning_triggers(
        current_composite=58.0,
        predicted_next_high_prob=0.80,
        user_history_composites=[55.0, 56.0],  # Trigger C
        last_alert_timestamp=last_alert_time,
        cooldown_days=14
    )
    assert res_urgent["alert_triggered"] is True
    assert res_urgent["severity"] == "Urgent"
