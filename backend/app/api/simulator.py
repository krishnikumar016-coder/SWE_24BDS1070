from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app import models, schemas, security
from app.core.simulator_engine import run_what_if_simulation

router = APIRouter(prefix="/simulator", tags=["What-If Simulator"])

@router.post("/simulate", response_model=schemas.SimulatorResponse)
def simulate_intervention(
    sim_in: schemas.SimulatorRequest,
    current_user: models.User = Depends(security.require_roles(["HR", "Admin"])),
    db: Session = Depends(get_db)
):
    """
    Runs What-If Intervention Simulation for HR/Admin users.
    If employee_id is specified, verifies consent check or audit logging.
    """
    base_history = None
    if sim_in.user_id:
        target_user = db.query(models.User).filter(models.User.id == sim_in.user_id).first()
        if not target_user:
            raise HTTPException(status_code=404, detail="Target employee not found")

        # Consent check for individual data access
        latest_consent = (
            db.query(models.ConsentRecord)
            .filter(models.ConsentRecord.user_id == target_user.id)
            .order_by(models.ConsentRecord.timestamp.desc())
            .first()
        )
        opted_in = latest_consent.hr_data_sharing_opt_in if latest_consent else False
        if not opted_in:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Employee has not opted in to sharing individual data for simulation."
            )

        # Audit Log
        audit = models.AuditLog(
            actor_id=current_user.id,
            target_user_id=target_user.id,
            action="HR_WHAT_IF_SIMULATION",
            details_json={
                "overtime_hours": sim_in.overtime_hours,
                "workload_index": sim_in.workload_index
            }
        )
        db.add(audit)
        db.commit()

    result = run_what_if_simulation(
        overtime_hours=sim_in.overtime_hours,
        avg_weekly_hours=sim_in.avg_weekly_hours,
        workload_index=sim_in.workload_index,
        wfh_days_ratio=sim_in.wfh_days_ratio,
        leave_days_taken=sim_in.leave_days_taken,
        base_user_history=base_history
    )
    return result
