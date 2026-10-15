import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field

# Auth & User Schemas
class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    email: str
    role: str
    full_name: str

class TokenData(BaseModel):
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "Employee"  # "Employee", "HR", "Admin"
    department_id: Optional[int] = None
    client_contact_role: bool = True

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str
    department_id: Optional[int] = None
    client_contact_role: bool
    created_at: datetime.datetime
    current_consent: Optional[bool] = False

    class Config:
        from_attributes = True

# Consent Schemas
class ConsentCreate(BaseModel):
    hr_data_sharing_opt_in: bool

class ConsentOut(BaseModel):
    id: int
    user_id: int
    hr_data_sharing_opt_in: bool
    timestamp: datetime.datetime
    ip_address: Optional[str] = None

    class Config:
        from_attributes = True

# Department Schemas
class DepartmentOut(BaseModel):
    id: int
    name: str
    code: str

    class Config:
        from_attributes = True

class DepartmentCreate(BaseModel):
    name: str
    code: str

# Questionnaire Schemas
class AssessmentItemAnswer(BaseModel):
    item_id: str
    raw_answer: str

class AssessmentCreate(BaseModel):
    answers: List[AssessmentItemAnswer]

class AssessmentResponseOut(BaseModel):
    item_id: str
    raw_answer: str
    numeric_score: float

    class Config:
        from_attributes = True

class AssessmentOut(BaseModel):
    id: int
    user_id: int
    timestamp: datetime.datetime
    status: str
    personal_score: Optional[float] = None
    work_score: Optional[float] = None
    client_score: Optional[float] = None
    composite_score: Optional[float] = None
    risk_category: Optional[str] = None
    supplementary_scores_json: Optional[Dict[str, float]] = None
    responses: Optional[List[AssessmentResponseOut]] = None

    class Config:
        from_attributes = True

# Objective Indicator Schemas
class ObjectiveIndicatorCreate(BaseModel):
    avg_weekly_hours: float = 40.0
    overtime_hours: float = 0.0
    overtime_days: float = 0.0
    leave_days_taken: float = 0.0
    days_since_last_leave: float = 30.0
    wfh_days_ratio: float = 0.2
    workload_index: float = 0.5
    meeting_hours: float = 5.0

class ObjectiveIndicatorOut(BaseModel):
    id: int
    user_id: int
    timestamp: datetime.datetime
    avg_weekly_hours: float
    overtime_hours: float
    overtime_days: float
    leave_days_taken: float
    days_since_last_leave: float
    wfh_days_ratio: float
    workload_index: float
    meeting_hours: float

    class Config:
        from_attributes = True

# Early Warning Alert Schemas
class AlertOut(BaseModel):
    id: int
    user_id: int
    assessment_id: Optional[int]
    timestamp: datetime.datetime
    severity: str
    triggers_fired_json: List[str]
    top_drivers_json: List[Dict[str, Any]]
    status: str

    class Config:
        from_attributes = True

class AlertStatusUpdate(BaseModel):
    status: str  # "acknowledged", "resolved"

# Intervention Schemas
class InterventionOut(BaseModel):
    id: int
    user_id: int
    alert_id: Optional[int]
    assessment_id: Optional[int]
    target_role: str
    category: str
    title: str
    description: str
    actions_json: Optional[List[str]]
    status: str
    pre_composite: Optional[float]
    post_composite: Optional[float]
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class InterventionStatusUpdate(BaseModel):
    status: str  # "accepted", "completed"

# Simulator Schemas
class SimulatorRequest(BaseModel):
    user_id: Optional[int] = None
    department_id: Optional[int] = None
    overtime_hours: float
    avg_weekly_hours: float
    workload_index: float
    wfh_days_ratio: float
    leave_days_taken: float

class SimulatorResponse(BaseModel):
    baseline_risk_prob: float
    simulated_risk_prob: float
    risk_delta: float
    confidence_interval: List[float]  # [lower, upper]
    disclaimer: str

# HR Aggregates Schema
class DepartmentAggregateOut(BaseModel):
    department_id: int
    department_name: str
    sample_size: int  # suppressed if < 5 (k-anonymity)
    is_suppressed: bool
    risk_tier_counts: Optional[Dict[str, int]] = None
    risk_tier_percentages: Optional[Dict[str, float]] = None
    avg_composite_score: Optional[float] = None
    avg_personal_score: Optional[float] = None
    avg_work_score: Optional[float] = None
    avg_client_score: Optional[float] = None
    alert_counts: Optional[Dict[str, int]] = None
    intervention_effectiveness: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
