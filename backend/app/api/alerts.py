from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, security

router = APIRouter(prefix="/alerts", tags=["Early Warning Alerts"])

@router.get("/me", response_model=List[schemas.AlertOut])
def get_user_alerts(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns personal early-warning alerts for the logged-in employee.
    """
    alerts = (
        db.query(models.EarlyWarningAlert)
        .filter(models.EarlyWarningAlert.user_id == current_user.id)
        .order_by(models.EarlyWarningAlert.timestamp.desc())
        .all()
    )
    return alerts

@router.patch("/{alert_id}/status", response_model=schemas.AlertOut)
def update_alert_status(
    alert_id: int,
    status_update: schemas.AlertStatusUpdate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    alert = (
        db.query(models.EarlyWarningAlert)
        .filter(models.EarlyWarningAlert.id == alert_id, models.EarlyWarningAlert.user_id == current_user.id)
        .first()
    )
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    alert.status = status_update.status
    db.commit()
    db.refresh(alert)
    return alert
