import os
import json
import random
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple

from app.core.scoring import compute_cbi_scores, CBI_CONFIG

# Calibrated Norm Targets from published literature (PUMA / Danish norms)
NORM_TARGETS = {
    "personal_mean": 32.0,
    "personal_sd": 15.0,
    "work_mean": 33.0,
    "work_sd": 16.0,
    "client_mean": 31.0,
    "client_sd": 16.0,
    "high_risk_pct_min": 15.0,
    "high_risk_pct_max": 25.0
}

def scale_to_item_answer(subscale_score: float, scale_type: str, reverse: bool = False) -> str:
    """
    Maps continuous subscale score (0-100) + noise to categorical CBI options.
    """
    # Add small noise to vary item responses around the subscale mean
    noisy_val = np.clip(subscale_score + np.random.normal(0, 10), 0, 100)
    
    if reverse:
        # Reversed: 0 -> Always, 25 -> Often, 50 -> Sometimes, 75 -> Seldom, 100 -> Never/almost never
        if noisy_val < 12.5:
            return "Always"
        elif noisy_val < 37.5:
            return "Often"
        elif noisy_val < 62.5:
            return "Sometimes"
        elif noisy_val < 87.5:
            return "Seldom"
        else:
            return "Never/almost never"
    else:
        # Standard: 100 -> Always/To a very high degree, 75 -> Often/High, 50 -> Sometimes/Somewhat, 25 -> Seldom/Low, 0 -> Never/Very low
        if scale_type == "FREQ":
            if noisy_val >= 87.5:
                return "Always"
            elif noisy_val >= 62.5:
                return "Often"
            elif noisy_val >= 37.5:
                return "Sometimes"
            elif noisy_val >= 12.5:
                return "Seldom"
            else:
                return "Never/almost never"
        else:  # INTENSITY
            if noisy_val >= 87.5:
                return "To a very high degree"
            elif noisy_val >= 62.5:
                return "To a high degree"
            elif noisy_val >= 37.5:
                return "Somewhat"
            elif noisy_val >= 12.5:
                return "To a low degree"
            else:
                return "To a very low degree"

def generate_synthetic_dataset(
    num_employees: int = 400,
    num_windows: int = 15,
    seed: int = 42
) -> pd.DataFrame:
    """
    Generates synthetic longitudinal burnout dataset based on JD-R model.
    Returns pandas DataFrame with employee windows, objective indicators, item responses, and scored CBI metrics.
    """
    np.random.seed(seed)
    random.seed(seed)
    
    records = []
    
    departments = [1, 2, 3, 4]  # Eng, Sales, HR, CS
    
    for emp_id in range(1, num_employees + 1):
        dept_id = random.choice(departments)
        has_client_contact = (dept_id in [2, 4])  # Sales & CS have client contact
        
        # Per-employee baseline personality / trait factors
        trait_workload = np.random.uniform(0.2, 0.9)
        trait_resilience = np.random.uniform(0.7, 1.3)
        trait_hours = np.random.normal(40, 5)
        
        # Previous window state tracking for autocorrelation
        prev_personal = np.random.normal(32, 15)
        prev_work = np.random.normal(33, 15)
        prev_client = np.random.normal(31, 15) if has_client_contact else None
        
        in_intervention = False
        intervention_effect = 0.0

        for w in range(1, num_windows + 1):
            # Seasonality: deadline spike at window 5, 9, 13
            is_deadline = (w in [5, 9, 13])
            deadline_mult = 1.45 if is_deadline else 1.0
            
            # Objective demand indicators
            workload_idx = np.clip((trait_workload * deadline_mult + np.random.normal(0, 0.15)) - intervention_effect, 0.1, 1.0)
            avg_hours = max(35.0, trait_hours + (workload_idx - 0.5) * 20 - intervention_effect * 10)
            overtime_hrs = max(0.0, (avg_hours - 40.0) * 1.6 + np.random.normal(0, 3))
            overtime_days = min(5.0, max(0.0, overtime_hrs / 3.0))
            
            # Objective resource indicators
            days_since_leave = 15 * w if not in_intervention else max(5.0, 30.0 - w * 2)
            leave_taken = 2.0 if (w % 6 == 0 or in_intervention) else np.random.choice([0.0, 0.5, 1.0], p=[0.7, 0.2, 0.1])
            wfh_ratio = np.clip(np.random.beta(2, 5), 0.0, 1.0)
            meeting_hrs = np.clip(np.random.normal(6, 2) + workload_idx * 4, 1.0, 20.0)

            # JD-R Driven Target Subscales
            demand_score = 12.0 + ((avg_hours - 37) * 2.1) + (overtime_hrs * 2.1) + (workload_idx * 34.0)
            resource_score = (leave_taken * 3.0) + (wfh_ratio * 4.0) + ((trait_resilience - 1.0) * 12.0)
            
            target_personal = np.clip((demand_score * 0.95 - resource_score) / trait_resilience + np.random.normal(4, 9), 0, 100)
            target_work = np.clip((demand_score * 1.0 - resource_score) / trait_resilience + np.random.normal(4, 9), 0, 100)
            target_client = np.clip((demand_score * 0.90 - resource_score) / trait_resilience + np.random.normal(4, 9), 0, 100) if has_client_contact else None



            # Autocorrelation (alpha = 0.5)
            personal_score_target = np.clip(0.5 * prev_personal + 0.5 * target_personal, 0, 100)
            work_score_target = np.clip(0.5 * prev_work + 0.5 * target_work, 0, 100)
            client_score_target = np.clip(0.5 * prev_client + 0.5 * target_client, 0, 100) if has_client_contact else None
            
            prev_personal = personal_score_target
            prev_work = work_score_target
            if has_client_contact:
                prev_client = client_score_target

            # Generate item-level answers based on subscale targets
            answers = {}
            for item in CBI_CONFIG["subscales"]["personal"]["items"]:
                answers[item["id"]] = scale_to_item_answer(personal_score_target, item["scale"], item["reverse"])
                
            for item in CBI_CONFIG["subscales"]["work"]["items"]:
                answers[item["id"]] = scale_to_item_answer(work_score_target, item["scale"], item["reverse"])

            if has_client_contact:
                for item in CBI_CONFIG["subscales"]["client"]["items"]:
                    answers[item["id"]] = scale_to_item_answer(client_score_target, item["scale"], item["reverse"])

            # Supplementary items
            answers["S1"] = scale_to_item_answer(workload_idx * 100, "INTENSITY")
            answers["S2"] = scale_to_item_answer(100 - personal_score_target, "FREQ", reverse=True)
            answers["S3"] = scale_to_item_answer(trait_resilience * 50, "FREQ", reverse=True)
            answers["S4"] = scale_to_item_answer(100 - workload_idx * 80, "FREQ", reverse=True)
            answers["S5"] = scale_to_item_answer(100 - work_score_target, "FREQ", reverse=True)

            # Run REAL scoring code
            scores = compute_cbi_scores(answers, client_contact_role=has_client_contact)

            # Check if intervention triggers (if composite >= 50 and not already in intervention)
            if scores["composite_score"] and scores["composite_score"] >= 50.0 and not in_intervention:
                if random.random() < 0.6:  # 60% chance intervention is assigned
                    in_intervention = True
                    intervention_effect = 0.25  # lowers workload and overtime in future windows

            rec = {
                "user_id": emp_id,
                "department_id": dept_id,
                "client_contact_role": has_client_contact,
                "window": w,
                "timestamp": pd.Timestamp("2026-01-01") + pd.Timedelta(days=14 * (w - 1)),
                "avg_weekly_hours": round(avg_hours, 1),
                "overtime_hours": round(overtime_hrs, 1),
                "overtime_days": round(overtime_days, 1),
                "leave_days_taken": round(leave_taken, 1),
                "days_since_last_leave": round(days_since_leave, 1),
                "wfh_days_ratio": round(wfh_ratio, 2),
                "workload_index": round(workload_idx, 2),
                "meeting_hours": round(meeting_hrs, 1),
                "personal_score": scores["personal_score"],
                "work_score": scores["work_score"],
                "client_score": scores["client_score"],
                "composite_score": scores["composite_score"],
                "risk_category": scores["risk_category"],
                "is_high_risk": 1 if scores["risk_category"] == "High" else 0,
                "in_intervention": 1 if in_intervention else 0,
                "answers_json": json.dumps(answers)
            }
            records.append(rec)
            
    df = pd.DataFrame(records)
    return df

def verify_synthetic_calibration(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Checks generated dataset against published CBI norms and returns verification metrics.
    """
    p_mean = df["personal_score"].mean()
    p_sd = df["personal_score"].std()
    w_mean = df["work_score"].mean()
    w_sd = df["work_score"].std()
    
    client_df = df[df["client_score"].notna()]
    c_mean = client_df["client_score"].mean()
    c_sd = client_df["client_score"].std()
    
    high_pct = (df["is_high_risk"].sum() / len(df)) * 100.0
    
    checks = {
        "personal_mean": float(round(p_mean, 2)),
        "personal_sd": float(round(p_sd, 2)),
        "work_mean": float(round(w_mean, 2)),
        "work_sd": float(round(w_sd, 2)),
        "client_mean": float(round(c_mean, 2)),
        "client_sd": float(round(c_sd, 2)),
        "high_risk_pct": float(round(high_pct, 2)),
        "calibrated_pass": bool(
            (25 <= p_mean <= 40) and
            (25 <= w_mean <= 40) and
            (10 <= high_pct <= 30)
        )
    }
    return checks

if __name__ == "__main__":
    print("Generating synthetic dataset...")
    df = generate_synthetic_dataset(num_employees=400, num_windows=15)
    calib = verify_synthetic_calibration(df)
    print("Calibration checks:", json.dumps(calib, indent=2))
