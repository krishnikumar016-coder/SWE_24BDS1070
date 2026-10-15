import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas, security

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register_user(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Check department if provided
    if user_in.department_id:
        dept = db.query(models.Department).filter(models.Department.id == user_in.department_id).first()
        if not dept:
            raise HTTPException(status_code=400, detail="Department not found")

    hashed_pw = security.get_password_hash(user_in.password)
    new_user = models.User(
        email=user_in.email,
        password_hash=hashed_pw,
        full_name=user_in.full_name,
        role=user_in.role,
        department_id=user_in.department_id,
        client_contact_role=user_in.client_contact_role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Initial default consent record (opt-out by default)
    consent = models.ConsentRecord(
        user_id=new_user.id,
        hr_data_sharing_opt_in=False,
        timestamp=datetime.datetime.utcnow()
    )
    db.add(consent)
    db.commit()

    return new_user

@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = security.create_access_token(
        data={"sub": str(user.id), "email": user.email, "role": user.role}
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "email": user.email,
        "role": user.role,
        "full_name": user.full_name
    }

@router.get("/me", response_model=schemas.UserOut)
def get_current_user_profile(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    # Fetch latest consent state
    latest_consent = (
        db.query(models.ConsentRecord)
        .filter(models.ConsentRecord.user_id == current_user.id)
        .order_by(models.ConsentRecord.timestamp.desc())
        .first()
    )
    opt_in = latest_consent.hr_data_sharing_opt_in if latest_consent else False
    
    res = schemas.UserOut.from_orm(current_user)
    res.current_consent = opt_in
    return res

@router.post("/consent", response_model=schemas.ConsentOut)
def toggle_consent(
    consent_in: schemas.ConsentCreate,
    req: Request,
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    ip_addr = req.client.host if req.client else "127.0.0.1"
    new_consent = models.ConsentRecord(
        user_id=current_user.id,
        hr_data_sharing_opt_in=consent_in.hr_data_sharing_opt_in,
        timestamp=datetime.datetime.utcnow(),
        ip_address=ip_addr
    )
    db.add(new_consent)
    
    # Audit log
    audit = models.AuditLog(
        actor_id=current_user.id,
        target_user_id=current_user.id,
        action="CONSENT_TOGGLED",
        details_json={
            "hr_data_sharing_opt_in": consent_in.hr_data_sharing_opt_in,
            "ip_address": ip_addr
        }
    )
    db.add(audit)
    db.commit()
    db.refresh(new_consent)
    return new_consent

@router.get("/consent-history", response_model=list[schemas.ConsentOut])
def get_consent_history(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    records = (
        db.query(models.ConsentRecord)
        .filter(models.ConsentRecord.user_id == current_user.id)
        .order_by(models.ConsentRecord.timestamp.desc())
        .all()
    )
    return records

@router.get("/export-data")
def export_my_data(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    """
    GDPR Data Rights: Export all personal assessments, responses, indicators, alerts, and consent records.
    """
    assessments = db.query(models.Assessment).filter(models.Assessment.user_id == current_user.id).all()
    indicators = db.query(models.ObjectiveIndicator).filter(models.ObjectiveIndicator.user_id == current_user.id).all()
    alerts = db.query(models.EarlyWarningAlert).filter(models.EarlyWarningAlert.user_id == current_user.id).all()
    consents = db.query(models.ConsentRecord).filter(models.ConsentRecord.user_id == current_user.id).all()
    interventions = db.query(models.RecommendedIntervention).filter(models.RecommendedIntervention.user_id == current_user.id).all()

    return {
        "user_profile": {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role,
            "client_contact_role": current_user.client_contact_role
        },
        "consent_history": [schemas.ConsentOut.from_orm(c) for c in consents],
        "assessments": [schemas.AssessmentOut.from_orm(a) for a in assessments],
        "indicators": [schemas.ObjectiveIndicatorOut.from_orm(i) for i in indicators],
        "alerts": [schemas.AlertOut.from_orm(al) for al in alerts],
        "interventions": [schemas.InterventionOut.from_orm(iv) for iv in interventions]
    }

@router.delete("/delete-data", status_code=status.HTTP_200_OK)
def delete_my_data(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db)
):
    """
    GDPR Right to Be Forgotten: Permanently deletes all assessments, indicators, alerts, interventions, and user account.
    """
    user_id = current_user.id
    
    # Audit log entry before deletion
    audit = models.AuditLog(
        actor_id=user_id,
        target_user_id=user_id,
        action="USER_ACCOUNT_DELETED",
        details_json={"email": current_user.email}
    )
    db.add(audit)
    db.commit()

    # Cascade delete user records
    db.query(models.Assessment).filter(models.Assessment.user_id == user_id).delete()
    db.query(models.ObjectiveIndicator).filter(models.ObjectiveIndicator.user_id == user_id).delete()
    db.query(models.EarlyWarningAlert).filter(models.EarlyWarningAlert.user_id == user_id).delete()
    db.query(models.RecommendedIntervention).filter(models.RecommendedIntervention.user_id == user_id).delete()
    db.query(models.ConsentRecord).filter(models.ConsentRecord.user_id == user_id).delete()
    db.query(models.User).filter(models.User.id == user_id).delete()
    db.commit()

    return {"message": "All personal data and user account have been permanently deleted."}

