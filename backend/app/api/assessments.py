import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, security
from app.core.scoring import compute_cbi_scores, get_interleaved_questionnaire, CBI_CONFIG

router = APIRouter(prefix="/assessments", tags=["Assessments"])

@router.get("/config")
def get_assessment_config(
    current_user: models.User = Depends(security.get_current_user)
):
    """
    Returns questionnaire config with items interleaved/randomized as recommended by CBI authors.
    Filters out Client subscale if user does not have client_contact_role.
    """
    items = get_interleaved_questionnaire(client_contact_role=current_user.client_contact_role)
    return {
        "source_citation": CBI_CONFIG["source"],
        "cadence_days": CBI_CONFIG["assessment_cadence_days"],
        "cutoffs": CBI_CONFIG["cutoffs"],
        "disclaimer": "This tool is a screening and self-support aid, NOT a diagnostic instrument.",
        "items": items
    }

@router.post("", response_model=schemas.AssessmentOut, status_code=status.HTTP_201_CREATED)
def submit_assessment(
    assessment_in: schemas.AssessmentCreate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    # Convert input list to answers dict
    answers_dict = {ans.item_id: ans.raw_answer for ans in assessment_in.answers}
    
    # Compute CBI scores
    scores_result = compute_cbi_scores(
        answers=answers_dict,
        client_contact_role=current_user.client_contact_role
    )
    
    # Create Assessment DB Record
    assessment = models.Assessment(
        user_id=current_user.id,
        timestamp=datetime.datetime.utcnow(),
        status="completed",
        personal_score=scores_result["personal_score"],
        work_score=scores_result["work_score"],
        client_score=scores_result["client_score"],
        composite_score=scores_result["composite_score"],
        risk_category=scores_result["risk_category"],
        supplementary_scores_json=scores_result["supplementary_scores"]
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)

    # Store individual item responses
    item_responses = []
    for item_id, numeric_val in scores_result["item_scores"].items():
        raw_ans = answers_dict.get(item_id, "")
        resp = models.AssessmentResponse(
            assessment_id=assessment.id,
            item_id=item_id,
            raw_answer=raw_ans,
            numeric_score=numeric_val
        )
        item_responses.append(resp)
    db.add_all(item_responses)
    db.commit()
    db.refresh(assessment)

    # Automatically trigger closed-loop ML risk prediction, SHAP drivers, Early-Warning, and Recommendations
    try:
        import joblib
        import os
        from app.ml.trainer import MODEL_ARTIFACT_PATH
        from app.core.feature_builder import build_user_current_features
        from app.core.explainability import explain_prediction_shap
        from app.core.early_warning import evaluate_early_warning_triggers
        from app.core.interventions_engine import generate_recommendations_for_user

        if os.path.exists(MODEL_ARTIFACT_PATH):
            artifact = joblib.load(MODEL_ARTIFACT_PATH)
            model = artifact["model"]
            
            # Build current user feature row
            df_feat = build_user_current_features(db, current_user.id, assessment)
            pred_prob = float(model.predict_proba(df_feat)[:, 1][0])
            
            # SHAP top drivers
            top_drivers = explain_prediction_shap(model, df_feat, {})
            
            # Early Warning check
            past_assessments = (
                db.query(models.Assessment)
                .filter(models.Assessment.user_id == current_user.id)
                .order_by(models.Assessment.timestamp.asc())
                .all()
            )
            history_composites = [a.composite_score for a in past_assessments if a.composite_score is not None]
            
            # Get last alert timestamp for cooldown check
            last_alert = (
                db.query(models.EarlyWarningAlert)
                .filter(models.EarlyWarningAlert.user_id == current_user.id)
                .order_by(models.EarlyWarningAlert.timestamp.desc())
                .first()
            )
            last_alert_time = last_alert.timestamp if last_alert else None
            
            ew_result = evaluate_early_warning_triggers(
                current_composite=assessment.composite_score,
                predicted_next_high_prob=pred_prob,
                user_history_composites=history_composites[:-1], # past up to current
                last_alert_timestamp=last_alert_time
            )
            
            created_alert = None
            if ew_result.get("alert_triggered"):
                created_alert = models.EarlyWarningAlert(
                    user_id=current_user.id,
                    assessment_id=assessment.id,
                    timestamp=datetime.datetime.utcnow(),
                    severity=ew_result["severity"],
                    triggers_fired_json=ew_result["triggers"],
                    top_drivers_json=top_drivers,
                    status="open"
                )
                db.add(created_alert)
                db.commit()
                db.refresh(created_alert)
                
            # Generate recommendations
            generate_recommendations_for_user(
                db=db,
                user=current_user,
                alert=created_alert,
                assessment=assessment,
                top_drivers=top_drivers
            )
    except Exception as e:
        print(f"Error during closed-loop processing: {e}")

    return assessment


@router.get("/history", response_model=List[schemas.AssessmentOut])
def get_assessment_history(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    assessments = (
        db.query(models.Assessment)
        .filter(models.Assessment.user_id == current_user.id)
        .order_by(models.Assessment.timestamp.asc())
        .all()
    )
    return assessments

@router.get("/latest", response_model=schemas.AssessmentOut)
def get_latest_assessment(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    latest = (
        db.query(models.Assessment)
        .filter(models.Assessment.user_id == current_user.id)
        .order_by(models.Assessment.timestamp.desc())
        .first()
    )
    if not latest:
        raise HTTPException(status_code=404, detail="No assessment history found for user")
    return latest
