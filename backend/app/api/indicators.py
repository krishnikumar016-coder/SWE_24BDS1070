import io
import csv
import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, security

router = APIRouter(prefix="/indicators", tags=["Objective Indicators"])

# Design Principle: Non-invasive objective indicators only (hours, leave, WFH, workload).
# No monitoring of emails, messages, keystrokes, or screen activity.

@router.post("", response_model=schemas.ObjectiveIndicatorOut, status_code=status.HTTP_201_CREATED)
def create_objective_indicator(
    indicator_in: schemas.ObjectiveIndicatorCreate,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    now = datetime.datetime.utcnow()
    indicator = models.ObjectiveIndicator(
        user_id=current_user.id,
        timestamp=now,
        window_start=now - datetime.timedelta(days=14),
        window_end=now,
        avg_weekly_hours=indicator_in.avg_weekly_hours,
        overtime_hours=indicator_in.overtime_hours,
        overtime_days=indicator_in.overtime_days,
        leave_days_taken=indicator_in.leave_days_taken,
        days_since_last_leave=indicator_in.days_since_last_leave,
        wfh_days_ratio=indicator_in.wfh_days_ratio,
        workload_index=indicator_in.workload_index,
        meeting_hours=indicator_in.meeting_hours
    )
    db.add(indicator)
    db.commit()
    db.refresh(indicator)
    return indicator

@router.get("/history", response_model=List[schemas.ObjectiveIndicatorOut])
def get_indicator_history(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    indicators = (
        db.query(models.ObjectiveIndicator)
        .filter(models.ObjectiveIndicator.user_id == current_user.id)
        .order_by(models.ObjectiveIndicator.timestamp.asc())
        .all()
    )
    return indicators

@router.post("/import-csv", status_code=status.HTTP_201_CREATED)
async def import_indicators_csv(
    file: UploadFile = File(...),
    current_user: models.User = Depends(security.require_roles(["Admin", "HR"])),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    contents = await file.read()
    decoded = contents.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))
    
    imported_count = 0
    now = datetime.datetime.utcnow()
    
    for row in reader:
        email = row.get("user_email")
        user = db.query(models.User).filter(models.User.email == email).first()
        if not user:
            continue
            
        ind = models.ObjectiveIndicator(
            user_id=user.id,
            timestamp=now,
            window_start=now - datetime.timedelta(days=14),
            window_end=now,
            avg_weekly_hours=float(row.get("avg_weekly_hours", 40.0)),
            overtime_hours=float(row.get("overtime_hours", 0.0)),
            overtime_days=float(row.get("overtime_days", 0.0)),
            leave_days_taken=float(row.get("leave_days_taken", 0.0)),
            days_since_last_leave=float(row.get("days_since_last_leave", 30.0)),
            wfh_days_ratio=float(row.get("wfh_days_ratio", 0.2)),
            workload_index=float(row.get("workload_index", 0.5)),
            meeting_hours=float(row.get("meeting_hours", 5.0))
        )
        db.add(ind)
        imported_count += 1

    db.commit()
    return {"message": f"Successfully imported {imported_count} indicator records"}
