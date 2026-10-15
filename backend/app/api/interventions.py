from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, security
from app.core.interventions_engine import compute_intervention_effectiveness

router = APIRouter(prefix="/interventions", tags=["Interventions"])

@router.get("/me", response_model=List[schemas.InterventionOut])
def get_my_interventions(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns personalized interventions for logged-in employee.
    If no interventions exist but employee has taken an assessment, auto-generates recommendations.
    """
    interventions = (
        db.query(models.RecommendedIntervention)
        .filter(models.RecommendedIntervention.user_id == current_user.id)
        .order_by(models.RecommendedIntervention.created_at.desc())
        .all()
    )
    
    if not interventions:
        latest_assessment = (
            db.query(models.Assessment)
            .filter(models.Assessment.user_id == current_user.id)
            .order_by(models.Assessment.timestamp.desc())
            .first()
        )
        if latest_assessment:
            try:
                from app.core.interventions_engine import generate_recommendations_for_user
                default_drivers = [
                    {"dimension": "Workload", "feature": "workload_index"},
                    {"dimension": "Long Hours", "feature": "overtime_hours"}
                ]
                interventions = generate_recommendations_for_user(
                    db=db,
                    user=current_user,
                    alert=None,
                    assessment=latest_assessment,
                    top_drivers=default_drivers
                )
            except Exception as e:
                print(f"Error auto-generating recommendations: {e}")
                
    return interventions


@router.patch("/{intervention_id}/status", response_model=schemas.InterventionOut)
def update_intervention_status(
    intervention_id: int,
    status_in: schemas.InterventionStatusUpdate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    inter = (
        db.query(models.RecommendedIntervention)
        .filter(
            models.RecommendedIntervention.id == intervention_id,
            models.RecommendedIntervention.user_id == current_user.id
        )
        .first()
    )
    if not inter:
        raise HTTPException(status_code=404, detail="Intervention recommendation not found")

    inter.status = status_in.status
    if status_in.status == "completed":
        # Record latest composite as post_composite if available
        latest_assessment = (
            db.query(models.Assessment)
            .filter(models.Assessment.user_id == current_user.id)
            .order_by(models.Assessment.timestamp.desc())
            .first()
        )
        if latest_assessment:
            inter.post_composite = latest_assessment.composite_score

    db.commit()
    db.refresh(inter)
    return inter

@router.get("/effectiveness")
def get_effectiveness_report(
    current_user: models.User = Depends(security.require_roles(["HR", "Admin"])),
    db: Session = Depends(get_db)
):
    """
    Returns observational pre/post intervention effectiveness summary.
    """
    return compute_intervention_effectiveness(db)
