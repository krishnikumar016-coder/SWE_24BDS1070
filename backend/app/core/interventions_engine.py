import os
import yaml
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app import models

YAML_PATH = os.path.join(os.path.dirname(__file__), "..", "config_data", "interventions.yaml")

def load_interventions_config() -> Dict[str, Any]:
    with open(YAML_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

INTERVENTIONS_CONFIG = load_interventions_config()

def generate_recommendations_for_user(
    db: Session,
    user: models.User,
    alert: Optional[models.EarlyWarningAlert],
    assessment: models.Assessment,
    top_drivers: List[Dict[str, Any]]
) -> List[models.RecommendedIntervention]:
    """
    Generates personalized intervention recommendations for employee (and HR if employee opted-in).
    """
    rules = INTERVENTIONS_CONFIG["rules"]
    created_interventions = []
    
    # Identify dominant categories from top drivers
    categories = []
    for d in top_drivers:
        dim = d.get("dimension", "").lower()
        if "workload" in dim:
            categories.append("workload")
        elif "recovery" in dim:
            categories.append("recovery")
        elif "support" in dim:
            categories.append("support")
        elif "hours" in dim:
            categories.append("long_hours")
            
    if not categories:
        categories = ["workload", "recovery"]

    categories = list(dict.fromkeys(categories))[:2]  # top 2 distinct categories

    # Check if employee has opted in to sharing data with HR
    latest_consent = (
        db.query(models.ConsentRecord)
        .filter(models.ConsentRecord.user_id == user.id)
        .order_by(models.ConsentRecord.timestamp.desc())
        .first()
    )
    is_opted_in = latest_consent.hr_data_sharing_opt_in if latest_consent else False

    for cat in categories:
        rule_set = rules.get(cat, rules["workload"])
        
        # 1. Employee self-care recommendation (always created)
        emp_rule = rule_set["employee"]
        rec_emp = models.RecommendedIntervention(
            user_id=user.id,
            alert_id=alert.id if alert else None,
            assessment_id=assessment.id,
            target_role="Employee",
            category=cat,
            title=emp_rule["title"],
            description=emp_rule["description"],
            actions_json=emp_rule["actions"],
            status="suggested",
            pre_composite=assessment.composite_score
        )
        db.add(rec_emp)
        created_interventions.append(rec_emp)

        # 2. HR policy recommendation (ONLY created if employee has explicitly opted in)
        if is_opted_in:
            hr_rule = rule_set["hr"]
            rec_hr = models.RecommendedIntervention(
                user_id=user.id,
                alert_id=alert.id if alert else None,
                assessment_id=assessment.id,
                target_role="HR",
                category=cat,
                title=hr_rule["title"],
                description=hr_rule["description"],
                actions_json=hr_rule["actions"],
                status="suggested",
                pre_composite=assessment.composite_score
            )
            db.add(rec_hr)
            created_interventions.append(rec_hr)

    db.commit()
    for rec in created_interventions:
        db.refresh(rec)
    return created_interventions

def compute_intervention_effectiveness(db: Session) -> Dict[str, Any]:
    """
    Computes pre vs post composite score changes for completed interventions.
    Includes explicit observational caveat.
    """
    completed = (
        db.query(models.RecommendedIntervention)
        .filter(models.RecommendedIntervention.status == "completed")
        .all()
    )
    
    if not completed:
        return {
            "total_completed": 0,
            "avg_pre_composite": None,
            "avg_post_composite": None,
            "avg_delta": None,
            "caveat": "Observational association only. Changes in scores reflect pre/post assessment differences and cannot guarantee direct causal attribution."
        }

    deltas = []
    pre_scores = []
    post_scores = []
    
    for item in completed:
        if item.pre_composite is not None and item.post_composite is not None:
            pre_scores.append(item.pre_composite)
            post_scores.append(item.post_composite)
            deltas.append(item.post_composite - item.pre_composite)

    avg_pre = sum(pre_scores) / len(pre_scores) if pre_scores else 0.0
    avg_post = sum(post_scores) / len(post_scores) if post_scores else 0.0
    avg_delta = sum(deltas) / len(deltas) if deltas else 0.0

    return {
        "total_completed": len(completed),
        "avg_pre_composite": round(avg_pre, 2),
        "avg_post_composite": round(avg_post, 2),
        "avg_delta": round(avg_delta, 2),
        "caveat": "Observational association only. Changes in scores reflect pre/post assessment differences and cannot guarantee direct causal attribution."
    }
