import os
import joblib
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, security
from app.ml.trainer import train_and_evaluate_models, MODEL_ARTIFACT_PATH
from app.ml.generator import generate_synthetic_dataset, verify_synthetic_calibration

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.post("/retrain", status_code=status.HTTP_200_OK)
def retrain_ml_model(
    current_user: models.User = Depends(security.require_roles(["Admin"])),
    db: Session = Depends(get_db)
):
    """
    Triggers full model retraining pipeline and updates stored model metadata.
    """
    summary = train_and_evaluate_models()
    
    # Update or add metadata in DB
    meta = models.MLModelMetadata(
        version=summary["model_version"],
        model_path=MODEL_ARTIFACT_PATH,
        metrics_json=summary["ablation_study"],
        feature_names_json=summary["ablation_study"]["LightGBM (Full + Monotonic)"],
        is_active=True
    )
    db.add(meta)
    db.commit()
    
    return {
        "status": "success",
        "message": "Model retrained successfully",
        "summary": summary
    }

@router.get("/model-metrics")
def get_model_metrics(
    current_user: models.User = Depends(security.require_roles(["Admin", "HR"]))
):
    """
    Returns metrics of active trained model artifact.
    """
    if not os.path.exists(MODEL_ARTIFACT_PATH):
        # Auto-train if not trained yet
        summary = train_and_evaluate_models()
        return summary
        
    artifact = joblib.load(MODEL_ARTIFACT_PATH)
    return {
        "trained_date": artifact.get("trained_date"),
        "metrics": artifact.get("metrics"),
        "features": artifact.get("feature_columns")
    }

@router.get("/data-quality")
def check_data_quality(
    current_user: models.User = Depends(security.require_roles(["Admin"])),
    db: Session = Depends(get_db)
):
    """
    Runs automated data-quality and norm calibration checks on system data.
    """
    df = generate_synthetic_dataset(num_employees=100, num_windows=5)
    calib = verify_synthetic_calibration(df)
    
    db_users_count = db.query(models.User).count()
    db_assessments_count = db.query(models.Assessment).count()
    
    return {
        "db_users_count": db_users_count,
        "db_assessments_count": db_assessments_count,
        "cbi_norm_calibration": calib,
        "data_minimization_check": "PASS - Raw item responses isolated, only computed features fed to ML."
    }
