import datetime
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship
from app.database import Base

class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    
    users = relationship("User", back_populates="department")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="Employee")  # "Employee", "HR", "Admin"
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    client_contact_role = Column(Boolean, default=True)  # whether Client-related burnout section applies
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    department = relationship("Department", back_populates="users")
    consent_records = relationship("ConsentRecord", back_populates="user", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="user", cascade="all, delete-orphan")
    objective_indicators = relationship("ObjectiveIndicator", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("EarlyWarningAlert", back_populates="user", cascade="all, delete-orphan")
    interventions = relationship("RecommendedIntervention", back_populates="user", cascade="all, delete-orphan")

class ConsentRecord(Base):
    __tablename__ = "consent_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    hr_data_sharing_opt_in = Column(Boolean, nullable=False, default=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    ip_address = Column(String(50), nullable=True)

    user = relationship("User", back_populates="consent_records")

class QuestionnaireConfig(Base):
    __tablename__ = "questionnaire_configs"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(50), nullable=False, unique=True)
    config_json = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    status = Column(String(50), default="completed")  # "completed", "in_progress"
    
    # Computed Subscale Scores (0.0 to 100.0)
    personal_score = Column(Float, nullable=True)
    work_score = Column(Float, nullable=True)
    client_score = Column(Float, nullable=True)
    
    # Composite Score (Project-defined summary, mean of active subscales)
    composite_score = Column(Float, nullable=True)
    risk_category = Column(String(20), nullable=True)  # "Low", "Moderate", "High"
    
    # Supplementary Scores stored as dict e.g. {"workload_pressure": 60, "recovery_sleep": 40, ...}
    supplementary_scores_json = Column(JSON, nullable=True)

    user = relationship("User", back_populates="assessments")
    responses = relationship("AssessmentResponse", back_populates="assessment", cascade="all, delete-orphan")
    alerts = relationship("EarlyWarningAlert", back_populates="assessment", cascade="all, delete-orphan")
    interventions = relationship("RecommendedIntervention", back_populates="assessment", cascade="all, delete-orphan")

class AssessmentResponse(Base):
    __tablename__ = "assessment_responses"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=False, index=True)
    item_id = Column(String(50), nullable=False)  # P1..P6, W1..W7, C1..C6, S1..S5
    raw_answer = Column(String(100), nullable=False)  # string response selected by user
    numeric_score = Column(Float, nullable=False)  # converted score after reverse scoring (0-100)

    assessment = relationship("Assessment", back_populates="responses")

class ObjectiveIndicator(Base):
    __tablename__ = "objective_indicators"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    window_start = Column(DateTime, nullable=True)
    window_end = Column(DateTime, nullable=True)
    
    avg_weekly_hours = Column(Float, default=40.0)
    overtime_hours = Column(Float, default=0.0)
    overtime_days = Column(Float, default=0.0)
    leave_days_taken = Column(Float, default=0.0)
    days_since_last_leave = Column(Float, default=30.0)
    wfh_days_ratio = Column(Float, default=0.2)  # 0.0 to 1.0
    workload_index = Column(Float, default=0.5)   # 0.0 to 1.0
    meeting_hours = Column(Float, default=5.0)

    user = relationship("User", back_populates="objective_indicators")

class EarlyWarningAlert(Base):
    __tablename__ = "early_warning_alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    severity = Column(String(20), nullable=False)  # "Watch", "Warning", "Urgent"
    triggers_fired_json = Column(JSON, nullable=False)  # ["Trigger A: Prob rose 0.18", ...]
    top_drivers_json = Column(JSON, nullable=False)     # [{"feature": "...", "impact": "..."}]
    status = Column(String(20), default="open")          # "open", "acknowledged", "resolved"

    user = relationship("User", back_populates="alerts")
    assessment = relationship("Assessment", back_populates="alerts")
    interventions = relationship("RecommendedIntervention", back_populates="alert")

class RecommendedIntervention(Base):
    __tablename__ = "recommended_interventions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    alert_id = Column(Integer, ForeignKey("early_warning_alerts.id"), nullable=True)
    assessment_id = Column(Integer, ForeignKey("assessments.id"), nullable=True)
    
    target_role = Column(String(20), nullable=False)  # "Employee" or "HR"
    category = Column(String(50), nullable=False)     # "workload", "recovery", "support", "long_hours"
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    actions_json = Column(JSON, nullable=True)        # array of specific bullet actions
    status = Column(String(20), default="suggested")   # "suggested", "accepted", "completed"
    
    pre_composite = Column(Float, nullable=True)
    post_composite = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("User", back_populates="interventions")
    alert = relationship("EarlyWarningAlert", back_populates="interventions")
    assessment = relationship("Assessment", back_populates="interventions")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)  # e.g., "HR_VIEWED_INDIVIDUAL_DATA", "CONSENT_TOGGLED"
    details_json = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class MLModelMetadata(Base):
    __tablename__ = "ml_model_metadata"

    id = Column(Integer, primary_key=True, index=True)
    version = Column(String(50), nullable=False)
    model_path = Column(String(255), nullable=False)
    metrics_json = Column(JSON, nullable=False)
    feature_names_json = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
