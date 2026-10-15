import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app import models
from app.core.anonymity import compute_k_anonymous_department_aggregate

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_anonymity.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

def test_k_anonymity_suppression_under_5():
    db = TestingSessionLocal()
    try:
        # Create department
        dept = models.Department(name="Small Team", code="SMALL")
        db.add(dept)
        db.commit()
        db.refresh(dept)

        # Add 3 employees (< 5 threshold)
        for i in range(3):
            u = models.User(
                email=f"user{i}@small.com",
                password_hash="dummy",
                full_name=f"User {i}",
                role="Employee",
                department_id=dept.id
            )
            db.add(u)
        db.commit()

        # Compute aggregate
        res = compute_k_anonymous_department_aggregate(db, dept.id)
        assert res["is_suppressed"] is True
        assert res["sample_size"] == 3
        assert "suppressed for privacy" in res["message"]
        assert "avg_composite_score" not in res
    finally:
        db.close()

def test_k_anonymity_pass_5_or_more():
    db = TestingSessionLocal()
    try:
        # Create department
        dept = models.Department(name="Large Team", code="LARGE")
        db.add(dept)
        db.commit()
        db.refresh(dept)

        # Add 6 employees (>= 5 threshold)
        for i in range(6):
            u = models.User(
                email=f"user{i}@large.com",
                password_hash="dummy",
                full_name=f"User {i}",
                role="Employee",
                department_id=dept.id
            )
            db.add(u)
            db.commit()
            
            # Add assessment
            ass = models.Assessment(
                user_id=u.id,
                composite_score=40.0 + i,
                personal_score=40.0,
                work_score=40.0,
                risk_category="Moderate"
            )
            db.add(ass)
        db.commit()

        # Compute aggregate
        res = compute_k_anonymous_department_aggregate(db, dept.id)
        assert res["is_suppressed"] is False
        assert res["sample_size"] == 6
        assert res["avg_composite_score"] is not None
        assert res["risk_tier_counts"]["Moderate"] == 6
    finally:
        db.close()
