from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app import models
from app.config import settings

def compute_k_anonymous_department_aggregate(
    db: Session,
    department_id: int
) -> Dict[str, Any]:
    """
    Computes department-level burnout aggregates with server-side k-anonymity enforcement.
    If sample size N < K_ANONYMITY_THRESHOLD (default 5), suppresses individual metrics and returns message.
    """
    dept = db.query(models.Department).filter(models.Department.id == department_id).first()
    if not dept:
        return {"error": "Department not found"}

    users = db.query(models.User).filter(models.User.department_id == department_id, models.User.role == "Employee").all()
    sample_size = len(users)
    k_thresh = settings.K_ANONYMITY_THRESHOLD

    if sample_size < k_thresh:
        return {
            "department_id": department_id,
            "department_name": dept.name,
            "sample_size": sample_size,
            "is_suppressed": True,
            "message": f"Department group size (N={sample_size} < {k_thresh}) suppressed for privacy and k-anonymity compliance."
        }

    user_ids = [u.id for u in users]
    
    # Get latest completed assessment for each employee in department
    latest_assessments = []
    for uid in user_ids:
        ass = (
            db.query(models.Assessment)
            .filter(models.Assessment.user_id == uid)
            .order_by(models.Assessment.timestamp.desc())
            .first()
        )
        if ass and ass.composite_score is not None:
            latest_assessments.append(ass)

    if not latest_assessments:
        return {
            "department_id": department_id,
            "department_name": dept.name,
            "sample_size": sample_size,
            "is_suppressed": False,
            "avg_composite_score": None,
            "risk_tier_counts": {"Low": 0, "Moderate": 0, "High": 0},
            "risk_tier_percentages": {"Low": 0.0, "Moderate": 0.0, "High": 0.0}
        }

    total_ass = len(latest_assessments)
    tier_counts = {"Low": 0, "Moderate": 0, "High": 0}
    comp_sum = 0.0
    p_sum = 0.0
    w_sum = 0.0
    c_sum = 0.0
    c_count = 0

    for a in latest_assessments:
        tier_counts[a.risk_category] = tier_counts.get(a.risk_category, 0) + 1
        comp_sum += a.composite_score
        p_sum += (a.personal_score or 0.0)
        w_sum += (a.work_score or 0.0)
        if a.client_score is not None:
            c_sum += a.client_score
            c_count += 1

    tier_pcts = {cat: round((cnt / total_ass) * 100.0, 1) for cat, cnt in tier_counts.items()}

    # Alert counts for department
    alerts_count = (
        db.query(models.EarlyWarningAlert)
        .filter(models.EarlyWarningAlert.user_id.in_(user_ids))
        .count()
    )

    return {
        "department_id": department_id,
        "department_name": dept.name,
        "sample_size": sample_size,
        "is_suppressed": False,
        "avg_composite_score": round(comp_sum / total_ass, 2),
        "avg_personal_score": round(p_sum / total_ass, 2),
        "avg_work_score": round(w_sum / total_ass, 2),
        "avg_client_score": round(c_sum / c_count, 2) if c_count > 0 else None,
        "risk_tier_counts": tier_counts,
        "risk_tier_percentages": tier_pcts,
        "total_active_alerts": alerts_count
    }
