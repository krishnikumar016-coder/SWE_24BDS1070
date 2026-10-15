import datetime
from typing import List, Dict, Any, Optional

URGENT_SUPPORTIVE_MESSAGE = (
    "Your recent assessment indicates high fatigue and burnout indicators. "
    "Please take a moment to prioritize your health. We strongly encourage you to connect "
    "with professional support resources, Employee Assistance Programs (EAP), or a trusted advisor. "
    "Remember: This tool is a confidential self-support aid, NOT a diagnostic instrument or workplace evaluation tool."
)

def evaluate_early_warning_triggers(
    current_composite: float,
    predicted_next_high_prob: float,
    user_history_composites: List[float],
    last_alert_timestamp: Optional[datetime.datetime] = None,
    cooldown_days: int = 14
) -> Dict[str, Any]:
    """
    Evaluates personalized early-warning triggers against an employee's OWN history:
    - Trigger A: Predicted next-period High-risk probability rose by > 0.15 vs their baseline average.
    - Trigger B: Composite rose >= 10 points across the last 2 assessments, OR exceeds baseline + 1 SD.
    - Trigger C: Moderate or High risk (composite >= 35) for 3 consecutive assessments.
    
    Determines severity:
    - Urgent: Trigger C or composite >= 50 or predicted_prob >= 0.70
    - Warning: Trigger A or B with moderate risk (composite >= 35) or predicted_prob >= 0.45
    - Watch: Trigger A or B with low current risk (composite < 35)
    
    Applies cooldown deduplication to prevent alert fatigue.
    """
    if not user_history_composites:
        user_history_composites = [current_composite]
    else:
        user_history_composites = list(user_history_composites) + [current_composite]

    num_records = len(user_history_composites)
    baseline_avg = sum(user_history_composites[:max(1, min(3, num_records))]) / max(1, min(3, num_records))
    
    # Calculate SD
    if num_records > 1:
        variance = sum((x - baseline_avg) ** 2 for x in user_history_composites) / (num_records - 1)
        history_sd = variance ** 0.5
    else:
        history_sd = 10.0

    triggers_fired = []

    # Trigger A: Prob rose > 0.15 vs baseline
    # Estimate baseline probability as low (~0.15) if baseline score was low
    baseline_prob_est = 0.15 if baseline_avg < 35 else 0.35
    prob_rise = predicted_next_high_prob - baseline_prob_est
    if prob_rise > 0.15:
        triggers_fired.append(f"Trigger A: Predicted High-risk probability rose by {prob_rise:.2f} vs personal baseline.")

    # Trigger B: Rose >= 10 pts in last 2 assessments OR composite > baseline + 1 SD
    score_rose_10 = False
    if num_records >= 2:
        score_diff = current_composite - user_history_composites[-2]
        if score_diff >= 10.0:
            score_rose_10 = True
            triggers_fired.append(f"Trigger B: Composite score rose by {score_diff:.1f} points in the last 2 assessments.")

    exceeds_sd = False
    if current_composite > (baseline_avg + max(5.0, history_sd)):
        exceeds_sd = True
        triggers_fired.append(f"Trigger B: Composite score ({current_composite:.1f}) exceeds personal baseline + 1 SD ({baseline_avg + history_sd:.1f}).")

    # Trigger C: Moderate/High for 3 consecutive assessments
    moderate_high_consecutive = False
    if num_records >= 3:
        last_3 = user_history_composites[-3:]
        if all(score >= 35.0 for score in last_3):
            moderate_high_consecutive = True
            triggers_fired.append("Trigger C: Moderate or High burnout score sustained across 3 consecutive assessments.")

    if not triggers_fired:
        return {"alert_triggered": False, "severity": None, "triggers": [], "supportive_message": None}

    # Determine Severity Tier
    if current_composite >= 50.0 or moderate_high_consecutive or predicted_next_high_prob >= 0.65:
        severity = "Urgent"
    elif current_composite >= 35.0 or predicted_next_high_prob >= 0.40 or score_rose_10:
        severity = "Warning"
    else:
        severity = "Watch"

    # Cooldown Check (Deduplication)
    now = datetime.datetime.utcnow()
    is_cooldown_active = False
    if last_alert_timestamp:
        days_since_last = (now - last_alert_timestamp).days
        if days_since_last < cooldown_days and severity != "Urgent":
            is_cooldown_active = True

    if is_cooldown_active:
        return {
            "alert_triggered": False,
            "reason": f"Alert suppressed due to active {cooldown_days}-day cooldown period.",
            "severity": severity,
            "triggers": triggers_fired,
            "supportive_message": None
        }

    supportive_msg = URGENT_SUPPORTIVE_MESSAGE if severity == "Urgent" else None

    return {
        "alert_triggered": True,
        "severity": severity,
        "triggers": triggers_fired,
        "supportive_message": supportive_msg
    }
