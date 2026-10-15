import datetime
from sqlalchemy.orm import Session
from app import models, security

def seed_database(db: Session):
    # Seed Departments
    if db.query(models.Department).count() == 0:
        dept_eng = models.Department(name="Engineering", code="ENG")
        dept_sales = models.Department(name="Sales & Marketing", code="SALES")
        dept_hr = models.Department(name="Human Resources", code="HR")
        dept_cs = models.Department(name="Customer Support", code="CS")
        
        db.add_all([dept_eng, dept_sales, dept_hr, dept_cs])
        db.commit()

    # Seed Admin User
    admin = db.query(models.User).filter(models.User.email == "admin@company.com").first()
    if not admin:
        hr_dept = db.query(models.Department).filter(models.Department.code == "HR").first()
        admin = models.User(
            email="admin@company.com",
            password_hash=security.get_password_hash("admin123"),
            full_name="System Administrator",
            role="Admin",
            department_id=hr_dept.id if hr_dept else None,
            client_contact_role=False
        )
        db.add(admin)
        db.commit()

    # Seed HR User
    hr_user = db.query(models.User).filter(models.User.email == "hr@company.com").first()
    if not hr_user:
        hr_dept = db.query(models.Department).filter(models.Department.code == "HR").first()
        hr_user = models.User(
            email="hr@company.com",
            password_hash=security.get_password_hash("hr123456"),
            full_name="Jane HR Manager",
            role="HR",
            department_id=hr_dept.id if hr_dept else None,
            client_contact_role=False
        )
        db.add(hr_user)
        db.commit()

    # Seed Employee User
    emp1 = db.query(models.User).filter(models.User.email == "employee1@company.com").first()
    if not emp1:
        eng_dept = db.query(models.Department).filter(models.Department.code == "ENG").first()
        emp1 = models.User(
            email="employee1@company.com",
            password_hash=security.get_password_hash("emp123456"),
            full_name="John Dev",
            role="Employee",
            department_id=eng_dept.id if eng_dept else None,
            client_contact_role=True
        )
        db.add(emp1)
        db.commit()
        
        # Initial consent record
        consent = models.ConsentRecord(
            user_id=emp1.id,
            hr_data_sharing_opt_in=True,
            timestamp=datetime.datetime.utcnow()
        )
        db.add(consent)
        db.commit()

    print("Database seeding completed.")
