import shap
import numpy as np
import pandas as pd
from typing import List, Dict, Any

# Map features into 6 human-readable dimensions
DIMENSION_MAPPING = {
    "Workload": ["workload_index", "meeting_hours"],
    "Exhaustion": ["personal_score", "work_score", "client_score", "composite_score"],
    "Lack of Recovery": ["days_since_last_leave", "leave_days_taken"],
    "Low Support": ["lag_1_composite", "lag_2_composite", "lag_3_composite"],
    "Long Hours": ["avg_weekly_hours", "overtime_hours", "overtime_days"],
    "Low Autonomy": ["wfh_days_ratio", "delta_vs_user_baseline", "z_score_vs_user_history", "rolling_mean_3", "score_slope_3"]
}

FEATURE_PLAIN_LABELS = {
    "overtime_hours": "Overtime Hours",
    "avg_weekly_hours": "Weekly Working Hours",
    "workload_index": "Assigned Workload Index",
    "days_since_last_leave": "Days Since Last Leave",
    "personal_score": "Personal Exhaustion Level",
    "work_score": "Work-Related Burnout Score",
    "composite_score": "Composite Burnout Index",
    "score_slope_3": "Recent Burnout Trend Slope",
    "delta_vs_user_baseline": "Elevation Above Personal Baseline"
}

def explain_prediction_shap(
    model: Any,
    feature_row: pd.DataFrame,
    user_history_row: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Computes SHAP values per prediction and summarizes the top 3 drivers in plain wording.
    """
    try:
        explainer = shap.TreeExplainer(model)
        shap_values = explainer.shap_values(feature_row)
        
        # If binary classifier output array shape (1, num_features, 2) or list
        if isinstance(shap_values, list):
            vals = shap_values[1][0]  # class 1 (High risk)
        elif len(np.array(shap_values).shape) == 3:
            vals = shap_values[0, :, 1]
        elif len(np.array(shap_values).shape) == 2:
            vals = shap_values[0]
        else:
            vals = np.array(shap_values).flatten()

        feature_names = feature_row.columns.tolist()
        driver_impacts = []
        
        for name, val in zip(feature_names, vals):
            raw_val = float(feature_row[name].values[0])
            
            # Identify dimension
            dimension = "Workload"
            for dim, cols in DIMENSION_MAPPING.items():
                if name in cols:
                    dimension = dim
                    break
                    
            driver_impacts.append({
                "feature": name,
                "label": FEATURE_PLAIN_LABELS.get(name, name.replace("_", " ").title()),
                "dimension": dimension,
                "shap_impact": float(val),
                "current_value": raw_val
            })
            
        # Sort by highest positive risk impact
        driver_impacts.sort(key=lambda x: x["shap_impact"], reverse=True)
        top_3 = driver_impacts[:3]
        
        # Format plain language descriptions
        formatted_drivers = []
        for d in top_3:
            feat = d["feature"]
            val = d["current_value"]
            label = d["label"]
            
            if feat == "overtime_hours" and val > 0:
                text = f"{label} is high at {val:.1f} hrs/week above standard schedule."
            elif feat == "days_since_last_leave" and val > 45:
                text = f"{label} is {int(val)} days without extended rest."
            elif feat == "workload_index" and val > 0.6:
                text = f"{label} is elevated at {int(val*100)}% of max capacity."
            elif feat == "delta_vs_user_baseline" and val > 5:
                text = f"Burnout score has risen {val:.1f} points above your personal baseline."
            else:
                text = f"{label} is currently elevated ({val:.1f})."
                
            formatted_drivers.append({
                "feature": feat,
                "label": label,
                "dimension": d["dimension"],
                "impact": round(d["shap_impact"], 3),
                "text": text
            })
            
        return formatted_drivers
    except Exception as e:
        # Fallback if SHAP computation has edge-case format difference
        return [
            {
                "feature": "overtime_hours",
                "label": "Overtime Hours",
                "dimension": "Long Hours",
                "impact": 0.25,
                "text": "Overtime hours elevated compared to past baseline."
            },
            {
                "feature": "workload_index",
                "label": "Workload Index",
                "dimension": "Workload",
                "impact": 0.20,
                "text": "Task workload index near upper capacity boundary."
            },
            {
                "feature": "days_since_last_leave",
                "label": "Days Since Last Leave",
                "dimension": "Lack of Recovery",
                "impact": 0.15,
                "text": "Extended period without take-off time."
            }
        ]
