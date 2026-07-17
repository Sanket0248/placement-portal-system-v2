"""
models.py — SQLAlchemy database models (ORM layer).

Defines six tables that map to Python classes:
  User           — login credentials + role (admin / student / company)
  Student        — student profile linked to a User
  Company        — company profile linked to a User
  PlacementDrive — a job posting created by a company
  Application    — a student applying to a specific drive
  Interview      — interview details for an application

Relationships:
  User  1───1  Student       (one user has one student profile)
  User  1───1  Company       (one user has one company profile)
  Company  1───*  PlacementDrive  (a company posts many drives)
  PlacementDrive  1───*  Application   (a drive receives many applications)
  Student  1───*  Application          (a student submits many applications)
  Application  1───0..1  Interview     (an application may have one interview)
"""

from datetime import datetime, date, timezone

from extensions import db


def utcnow():
    """
    Return the current UTC time as a timezone-aware datetime.

    Python's datetime.utcnow() is deprecated because it returns a "naive"
    datetime (no timezone info). This replacement is future-proof.
    """
    return datetime.now(timezone.utc)


# ═══════════════════════════════════════════════════════════════
#  USER — authentication credentials + role
# ═══════════════════════════════════════════════════════════════
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)  # Werkzeug bcrypt hash
    role = db.Column(db.String(20), nullable=False, index=True)  # 'admin', 'student', 'company'
    is_active = db.Column(db.Boolean, default=True)       # False = account deactivated
    is_blacklisted = db.Column(db.Boolean, default=False)  # True = banned by admin
    created_at = db.Column(db.DateTime, default=utcnow)

    # One-to-one relationships: a User is EITHER a student OR a company (never both).
    # uselist=False means user.student_profile returns a single Student, not a list.
    student_profile = db.relationship('Student', backref='user', uselist=False)
    company_profile = db.relationship('Company', backref='user', uselist=False)

    def to_dict(self):
        """Serialize to a JSON-safe dictionary (used in API responses)."""
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'is_active': self.is_active,
            'is_blacklisted': self.is_blacklisted,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# ═══════════════════════════════════════════════════════════════
#  STUDENT — profile details for student users
# ═══════════════════════════════════════════════════════════════
class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    full_name = db.Column(db.String(100), nullable=False)
    roll_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    branch = db.Column(db.String(50), nullable=False, index=True)  # CS, IT, ECE, etc.
    cgpa = db.Column(db.Float, nullable=False)        # 0.0 – 10.0
    year_of_study = db.Column(db.Integer, nullable=False)  # 1, 2, 3, or 4
    phone = db.Column(db.String(15))
    resume_path = db.Column(db.String(255))  # filename in uploads/ folder
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    # A student can have many applications (one per drive they apply to).
    applications = db.relationship('Application', backref='student', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'full_name': self.full_name,
            'roll_number': self.roll_number,
            'branch': self.branch,
            'cgpa': self.cgpa,
            'year_of_study': self.year_of_study,
            'phone': self.phone,
            'resume_path': self.resume_path,
        }


# ═══════════════════════════════════════════════════════════════
#  COMPANY — profile details for recruiter/company users
# ═══════════════════════════════════════════════════════════════
class Company(db.Model):
    __tablename__ = 'companies'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    company_name = db.Column(db.String(100), nullable=False)
    hr_name = db.Column(db.String(100), nullable=False)
    hr_email = db.Column(db.String(120), nullable=False)
    website = db.Column(db.String(200))
    industry = db.Column(db.String(100))
    description = db.Column(db.Text)
    # Admin must approve a company before it can create placement drives.
    approval_status = db.Column(db.String(20), default='pending', index=True)  # pending/approved/rejected
    registered_at = db.Column(db.DateTime, default=utcnow)

    # A company can post many placement drives.
    drives = db.relationship('PlacementDrive', backref='company', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'company_name': self.company_name,
            'hr_name': self.hr_name,
            'hr_email': self.hr_email,
            'website': self.website,
            'industry': self.industry,
            'description': self.description,
            'approval_status': self.approval_status,
            'registered_at': self.registered_at.isoformat() if self.registered_at else None,
        }


# ═══════════════════════════════════════════════════════════════
#  PLACEMENT DRIVE — a job/internship posting by a company
# ═══════════════════════════════════════════════════════════════
class PlacementDrive(db.Model):
    __tablename__ = 'placement_drives'

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False, index=True)
    job_title = db.Column(db.String(100), nullable=False)
    job_description = db.Column(db.Text, nullable=False)
    # Comma-separated branch codes, e.g. "CS,IT,ECE"
    eligible_branches = db.Column(db.String(200), nullable=False)
    min_cgpa = db.Column(db.Float, nullable=False)       # Minimum CGPA to apply
    eligible_year = db.Column(db.Integer, nullable=False)  # Which year students can apply
    application_deadline = db.Column(db.Date, nullable=False)
    # Drive lifecycle: pending → approved (by admin) → closed (by company/admin)
    #                  pending → rejected (by admin)
    status = db.Column(db.String(20), default='pending', index=True)
    job_type = db.Column(db.String(50))   # Full-time, Internship, Contract
    package_lpa = db.Column(db.Float)     # Annual salary in Lakhs Per Annum
    created_at = db.Column(db.DateTime, default=utcnow)

    # A drive receives many applications from students.
    applications = db.relationship('Application', backref='drive', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'company_id': self.company_id,
            'job_title': self.job_title,
            'job_description': self.job_description,
            # Split the comma-separated string back into a list for the frontend.
            'eligible_branches': self.eligible_branches.split(','),
            'min_cgpa': self.min_cgpa,
            'eligible_year': self.eligible_year,
            'application_deadline': self.application_deadline.isoformat(),
            'status': self.status,
            'job_type': self.job_type,
            'package_lpa': self.package_lpa,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


# ═══════════════════════════════════════════════════════════════
#  APPLICATION — a student's application to a specific drive
# ═══════════════════════════════════════════════════════════════
class Application(db.Model):
    __tablename__ = 'applications'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, index=True)
    drive_id = db.Column(db.Integer, db.ForeignKey('placement_drives.id'), nullable=False, index=True)
    application_date = db.Column(db.Date, default=date.today)
    # Status flow: applied → shortlisted → selected  (happy path)
    #              applied → shortlisted → rejected   (not selected)
    #              applied → rejected                  (rejected early)
    status = db.Column(db.String(20), default='applied', index=True)
    # Snapshot of the resume filename at the time of applying.
    resume_snapshot = db.Column(db.String(255))
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)

    # Prevent a student from applying to the same drive twice.
    __table_args__ = (
        db.UniqueConstraint('student_id', 'drive_id', name='unique_student_drive'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'drive_id': self.drive_id,
            'application_date': self.application_date.isoformat(),
            'status': self.status,
            'resume_snapshot': self.resume_snapshot,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            # Include interview details if one exists (nested dict or None).
            'interview': self.interview.to_dict() if self.interview else None,
        }


# ═══════════════════════════════════════════════════════════════
#  INTERVIEW — scheduled by the company for a shortlisted applicant
# ═══════════════════════════════════════════════════════════════
class Interview(db.Model):
    __tablename__ = 'interviews'

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('applications.id'), nullable=False, index=True)
    scheduled_at = db.Column(db.DateTime, nullable=False)   # When the interview takes place
    mode = db.Column(db.String(50), default='Online')       # Online, In-Person, Phone
    location = db.Column(db.String(200))  # Meet link or office address
    notes = db.Column(db.Text)            # Instructions for the candidate
    # Result: pending → passed (student selected) or failed (student rejected)
    result = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=utcnow)

    # One-to-one relationship: each application has at most one interview.
    # uselist=False on the backref means application.interview returns one Interview or None.
    application = db.relationship('Application', backref=db.backref('interview', uselist=False))

    def to_dict(self):
        return {
            'id': self.id,
            'application_id': self.application_id,
            'scheduled_at': self.scheduled_at.isoformat(),
            'mode': self.mode,
            'location': self.location,
            'notes': self.notes,
            'result': self.result,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
