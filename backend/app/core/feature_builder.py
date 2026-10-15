import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional

FEATURE_COLUMNS = [
    # Current objective indicators
    "avg_weekly_hours",
    "overtime_hours",
    "overtime_days",
    "leave_days_taken",
    "days_since_last_leave",
    "wfh_days_ratio",
    "workload_index",
    "meeting_hours",
    
    # Current scores
    "personal_score",
    "work_score",
    "client_score",
    "composite_score",
    
    # Historical lag features (1 to 3 windows)
    "lag_1_composite",
    "lag_2_composite",
    "lag_3_composite",
    
    # Summary statistics
    "rolling_mean_3",
    "score_slope_3",
    "delta_vs_user_baseline",
    "z_score_vs_user_history"
]

# Monotonic positive constraints for demand features (index matched to FEATURE_COLUMNS)
# 1 = positive constraint (increasing feature value can only increase predicted risk probability), 0 = unconstrained
MONOTONIC_CONSTRAINTS = [
    1, # avg_weekly_hours
    1, # overtime_hours
    1, # overtime_days
   -1, # leave_days_taken (more leave reduces/maintains risk)
    1, # days_since_last_leave
    0, # wfh_days_ratio
    1, # workload_index
    1, # meeting_hours
    1, # personal_score
    1, # work_score
    1, # client_score
    1, # composite_score
    0, # lag_1_composite
    0, # lag_2_composite
    0, # lag_3_composite
    0, # rolling_mean_3
    1, # score_slope_3
    1, # delta_vs_user_baseline
    1  # z_score_vs_user_history
]

def build_features_from_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Constructs ML feature dataset from raw longitudinal records.
    Assumes df is sorted by user_id and window/timestamp.
    Creates NEXT-period target variables:
    - target_next_high (binary 0/1)
    - target_next_composite (float)
    """
    df = df.sort_values(["user_id", "window"]).copy()
    
    # Replace NaN client scores with 0 or fill forward if missing
    df["client_score_filled"] = df["client_score"].fillna(0.0)
    
    feature_rows = []
    
    for user_id, user_group in df.groupby("user_id"):
        user_group = user_group.reset_index(drop=True)
        num_obs = len(user_group)
        
        # Calculate user's personal baseline (mean of first 3 windows or all available up to window)
        user_baseline_mean = user_group["composite_score"].iloc[:max(1, min(3, num_obs))].mean()
        user_history_std = user_group["composite_score"].std()
        if pd.isna(user_history_std) or user_history_std == 0:
            user_history_std = 1.0

        for i in range(num_obs):
            row = user_group.iloc[i].to_dict()
            
            # Target is the NEXT assessment window (i + 1)
            if i < num_obs - 1:
                next_row = user_group.iloc[i + 1]
                target_next_composite = float(next_row["composite_score"])
                target_next_high = 1 if target_next_composite >= 50.0 else 0
            else:
                target_next_composite = np.nan
                target_next_high = np.nan

            # Lags
            lag_1 = float(user_group["composite_score"].iloc[i-1]) if i >= 1 else float(row["composite_score"])
            lag_2 = float(user_group["composite_score"].iloc[i-2]) if i >= 2 else lag_1
            lag_3 = float(user_group["composite_score"].iloc[i-3]) if i >= 3 else lag_2

            # Rolling stats over last 3 windows up to current
            recent_scores = user_group["composite_score"].iloc[max(0, i-2):i+1].values
            rolling_mean_3 = float(np.mean(recent_scores))
            
            # Slope over last 3 windows
            if len(recent_scores) > 1:
                x = np.arange(len(recent_scores))
                slope, _ = np.polyfit(x, recent_scores, 1)
            else:
                slope = 0.0

            # Delta vs personal baseline
            delta_vs_baseline = float(row["composite_score"] - user_baseline_mean)
            
            # Z-score vs personal history
            z_score = float((row["composite_score"] - user_baseline_mean) / user_history_std)

            feat = {
                "user_id": user_id,
                "window": row["window"],
                "timestamp": row["timestamp"],
                "department_id": row.get("department_id", 1),
                
                # Objective indicators
                "avg_weekly_hours": float(row["avg_weekly_hours"]),
                "overtime_hours": float(row["overtime_hours"]),
                "overtime_days": float(row["overtime_days"]),
                "leave_days_taken": float(row["leave_days_taken"]),
                "days_since_last_leave": float(row["days_since_last_leave"]),
                "wfh_days_ratio": float(row["wfh_days_ratio"]),
                "workload_index": float(row["workload_index"]),
                "meeting_hours": float(row["meeting_hours"]),
                
                # Subscale scores
                "personal_score": float(row["personal_score"]),
                "work_score": float(row["work_score"]),
                "client_score": float(row["client_score_filled"]),
                "composite_score": float(row["composite_score"]),
                
                # Lag & Trend features
                "lag_1_composite": lag_1,
                "lag_2_composite": lag_2,
                "lag_3_composite": lag_3,
                "rolling_mean_3": rolling_mean_3,
                "score_slope_3": float(slope),
                "delta_vs_user_baseline": delta_vs_baseline,
                "z_score_vs_user_history": z_score,
                
                # Next-period targets
                "target_next_composite": target_next_composite,
                "target_next_high": target_next_high
            }
            feature_rows.append(feat)

    feature_df = pd.DataFrame(feature_rows)
    return feature_df

def build_user_current_features(db: Any, user_id: int, current_assessment: Any) -> pd.DataFrame:
    """
    Builds a single-row feature DataFrame for the specified user and assessment.
    Used for online SHAP explainability and early warning evaluation upon assessment submission.
    """
    from app import models
    
    # 1. Fetch latest objective indicators
    ind = (
        db.query(models.ObjectiveIndicator)
        .filter(models.ObjectiveIndicator.user_id == user_id)
        .order_by(models.ObjectiveIndicator.timestamp.desc())
        .first()
    )
    
    avg_hours = ind.avg_weekly_hours if ind else 42.0
    overtime_hrs = ind.overtime_hours if ind else 4.0
    overtime_days = ind.overtime_days if ind else 1.5
    leave_taken = ind.leave_days_taken if ind else 0.0
    days_since_leave = ind.days_since_last_leave if ind else 30.0
    wfh_ratio = ind.wfh_days_ratio if ind else 0.2
    workload_idx = ind.workload_index if ind else 0.6
    meeting_hrs = ind.meeting_hours if ind else 5.0
    
    # 2. Fetch past assessment scores
    past_assessments = (
        db.query(models.Assessment)
        .filter(models.Assessment.user_id == user_id)
        .order_by(models.Assessment.timestamp.asc())
        .all()
    )
    
    past_composites = [a.composite_score for a in past_assessments if a.composite_score is not None]
    if not past_composites:
        past_composites = [current_assessment.composite_score]
        
    num_obs = len(past_composites)
    user_baseline_mean = float(np.mean(past_composites[:max(1, min(3, num_obs))]))
    user_history_std = float(np.std(past_composites)) if num_obs > 1 else 10.0
    if user_history_std == 0:
        user_history_std = 1.0

    curr_comp = float(current_assessment.composite_score or 0.0)
    p_score = float(current_assessment.personal_score or 0.0)
    w_score = float(current_assessment.work_score or 0.0)
    c_score = float(current_assessment.client_score or 0.0)

    lag_1 = float(past_composites[-2]) if num_obs >= 2 else curr_comp
    lag_2 = float(past_composites[-3]) if num_obs >= 3 else lag_1
    lag_3 = float(past_composites[-4]) if num_obs >= 4 else lag_2

    recent_scores = past_composites[-3:]
    rolling_mean_3 = float(np.mean(recent_scores))
    if len(recent_scores) > 1:
        x = np.arange(len(recent_scores))
        slope, _ = np.polyfit(x, recent_scores, 1)
    else:
        slope = 0.0

    delta_vs_baseline = curr_comp - user_baseline_mean
    z_score = (curr_comp - user_baseline_mean) / user_history_std

    row = {
        "avg_weekly_hours": avg_hours,
        "overtime_hours": overtime_hrs,
        "overtime_days": overtime_days,
        "leave_days_taken": leave_taken,
        "days_since_last_leave": days_since_leave,
        "wfh_days_ratio": wfh_ratio,
        "workload_index": workload_idx,
        "meeting_hours": meeting_hrs,
        "personal_score": p_score,
        "work_score": w_score,
        "client_score": c_score,
        "composite_score": curr_comp,
        "lag_1_composite": lag_1,
        "lag_2_composite": lag_2,
        "lag_3_composite": lag_3,
        "rolling_mean_3": rolling_mean_3,
        "score_slope_3": float(slope),
        "delta_vs_user_baseline": delta_vs_baseline,
        "z_score_vs_user_history": z_score
    }
    
    return pd.DataFrame([row])[FEATURE_COLUMNS]

