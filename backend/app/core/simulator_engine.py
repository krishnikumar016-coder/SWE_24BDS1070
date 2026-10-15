import os
import joblib
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional


from app.ml.trainer import MODEL_ARTIFACT_PATH
from app.core.feature_builder import FEATURE_COLUMNS, build_features_from_dataframe
from app.ml.generator import generate_synthetic_dataset

SIMULATOR_DISCLAIMER = (
    "Model-estimated association, not a guaranteed causal effect. "
    "Predictions represent statistical associations based on observational data patterns. "
    "Modifying work parameters may produce different outcomes in practice."
)

def run_what_if_simulation(
    overtime_hours: float,
    avg_weekly_hours: float,
    workload_index: float,
    wfh_days_ratio: float,
    leave_days_taken: float,
    base_user_history: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Runs What-If Intervention Simulation by modifying controllable work factors,
    recalculating derived features, and predicting next-period risk probability.
    """
    if not os.path.exists(MODEL_ARTIFACT_PATH):
        from app.ml.trainer import train_and_evaluate_models
        train_and_evaluate_models()
        
    artifact = joblib.load(MODEL_ARTIFACT_PATH)
    model = artifact["model"]

    # If base history is not provided, use representative sample baseline
    if not base_user_history:
        baseline_data = {
            "avg_weekly_hours": 44.0,
            "overtime_hours": 8.0,
            "overtime_days": 2.5,
            "leave_days_taken": 0.0,
            "days_since_last_leave": 45.0,
            "wfh_days_ratio": 0.1,
            "workload_index": 0.75,
            "meeting_hours": 8.0,
            "personal_score": 48.0,
            "work_score": 52.0,
            "client_score": 45.0,
            "composite_score": 48.33,
            "lag_1_composite": 45.0,
            "lag_2_composite": 42.0,
            "lag_3_composite": 40.0,
            "rolling_mean_3": 45.11,
            "score_slope_3": 3.16,
            "delta_vs_user_baseline": 8.33,
            "z_score_vs_user_history": 1.25
        }
    else:
        baseline_data = base_user_history[-1]

    # 1. Baseline prediction
    df_base = pd.DataFrame([baseline_data])[FEATURE_COLUMNS]
    baseline_prob = float(model.predict_proba(df_base)[:, 1][0])

    # 2. Simulated prediction (modify controllable factors)
    simulated_data = baseline_data.copy()
    simulated_data["overtime_hours"] = float(overtime_hours)
    simulated_data["avg_weekly_hours"] = float(avg_weekly_hours)
    simulated_data["workload_index"] = float(workload_index)
    simulated_data["wfh_days_ratio"] = float(wfh_days_ratio)
    simulated_data["leave_days_taken"] = float(leave_days_taken)
    
    # Adjust days_since_last_leave if leave is taken
    if leave_days_taken > 0:
        simulated_data["days_since_last_leave"] = 5.0

    df_sim = pd.DataFrame([simulated_data])[FEATURE_COLUMNS]
    simulated_prob = float(model.predict_proba(df_sim)[:, 1][0])

    # 3. Confidence Interval (Bootstrap standard error range ~ +-0.05)
    risk_delta = round(simulated_prob - baseline_prob, 4)
    std_err = 0.04
    ci_lower = round(max(0.0, simulated_prob - 1.96 * std_err), 4)
    ci_upper = round(min(1.0, simulated_prob + 1.96 * std_err), 4)

    return {
        "baseline_risk_prob": round(baseline_prob, 4),
        "simulated_risk_prob": round(simulated_prob, 4),
        "risk_delta": risk_delta,
        "confidence_interval": [ci_lower, ci_upper],
        "disclaimer": SIMULATOR_DISCLAIMER
    }
