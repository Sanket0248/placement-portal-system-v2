"""
routes/admin.py — Admin (placement cell) blueprint.

All endpoints require a valid JWT token from an admin user.
Prefix: /api/admin (set in app.py).

Endpoints:
  GET    /dashboard              — aggregate stats (cached 5 min)
  GET    /students               — list all students with user flags
  GET    /students/<id>          — single student detail
  PATCH  /students/<id>/blacklist — blacklist or reactivate a student
  GET    /companies              — list all companies
  GET    /companies/<id>         — single company detail
  PATCH  /companies/<id>/approve — approve a pending company
  PATCH  /companies/<id>/reject  — reject a pending company
  PATCH  /companies/<id>/blacklist — blacklist or reactivate a company
  GET    /drives                 — list all placement drives
  PATCH  /drives/<id>/approve    — approve a pending drive
  PATCH  /drives/<id>/reject     — reject a pending drive
  PATCH  /drives/<id>/close      — mark an approved drive as complete
  GET    /applications           — list all applications across all drives
  GET    /search?q=...&type=...  — search students and/or companies
  GET    /reports/monthly        — this month's summary stats
"""

from datetime import datetime, timezone

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.orm import joinedload

from extensions import db, cache
from models import User, Student, Company, PlacementDrive, Application

admin_bp = Blueprint('admin', __name__)


#Helper: verify the current user is an admin
def admin_required():
    """
    Check that the JWT-authenticated user has the 'admin' role.
    Returns (user, None, None) on success, or (None, error_response, status_code) on failure.
    """
    user = db.session.get(User, get_jwt_identity())
    if not user or user.role != 'admin':
        return None, jsonify({'error': 'Admin access required'}), 403
    return user, None, None


def _with_user_flags(profile, obj):
    """
    Merge a student/company profile dict with their parent User's
    email, is_active, and is_blacklisted flags (admin needs to see these).
    """
    data = profile.to_dict()
    data['email'] = obj.user.email
    data['is_active'] = obj.user.is_active
    data['is_blacklisted'] = obj.user.is_blacklisted
    return data


# Dashboard Stats (cached for 5 minutes to avoid repeated COUNT queries)
@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@cache.cached(timeout=300, key_prefix='admin_dashboard')
def dashboard():
    _, err, code = admin_required()
    if err:
        return err, code

    return jsonify({
        'total_students': Student.query.count(),
        'total_companies': Company.query.count(),
        'total_drives': PlacementDrive.query.count(),
        'pending_companies': Company.query.filter_by(approval_status='pending').count(),
        'pending_drives': PlacementDrive.query.filter_by(status='pending').count(),
        'total_applications': Application.query.count(),
        'selected_students': Application.query.filter_by(status='selected').count(),
    }), 200


# Students 
# joinedload(Student.user) eagerly loads the User in one SQL query
# instead of issuing a separate query for each student's user (N+1 fix).
@admin_bp.route('/students', methods=['GET'])
@jwt_required()
def get_students():
    _, err, code = admin_required()
    if err:
        return err, code

    students = Student.query.options(joinedload(Student.user)).all()
    return jsonify([_with_user_flags(s, s) for s in students]), 200


@admin_bp.route('/students/<int:id>', methods=['GET'])
@jwt_required()
def get_student(id):
    _, err, code = admin_required()
    if err:
        return err, code

    student = Student.query.options(joinedload(Student.user)).get_or_404(id)
    return jsonify(_with_user_flags(student, student)), 200


@admin_bp.route('/students/<int:id>/blacklist', methods=['PATCH'])
@jwt_required()
def blacklist_student(id):
    _, err, code = admin_required()
    if err:
        return err, code

    student = Student.query.get_or_404(id)
    data = request.get_json() or {}

    student.user.is_blacklisted = data.get('is_blacklisted', True)
    student.user.is_active = not student.user.is_blacklisted
    db.session.commit()

    status = 'blacklisted' if student.user.is_blacklisted else 'reactivated'
    return jsonify({'message': f'Student {status} successfully'}), 200


# Companies
@admin_bp.route('/companies', methods=['GET'])
@jwt_required()
def get_companies():
    _, err, code = admin_required()
    if err:
        return err, code

    companies = Company.query.options(joinedload(Company.user)).all()
    return jsonify([_with_user_flags(c, c) for c in companies]), 200


@admin_bp.route('/companies/<int:id>', methods=['GET'])
@jwt_required()
def get_company(id):
    _, err, code = admin_required()
    if err:
        return err, code

    company = Company.query.options(joinedload(Company.user)).get_or_404(id)
    data = company.to_dict()
    data['email'] = company.user.email
    return jsonify(data), 200


@admin_bp.route('/companies/<int:id>/approve', methods=['PATCH'])
@jwt_required()
def approve_company(id):
    _, err, code = admin_required()
    if err:
        return err, code

    company = Company.query.get_or_404(id)
    company.approval_status = 'approved'
    db.session.commit()
    cache.delete('admin_dashboard')
    return jsonify({'message': 'Company approved successfully'}), 200


@admin_bp.route('/companies/<int:id>/reject', methods=['PATCH'])
@jwt_required()
def reject_company(id):
    _, err, code = admin_required()
    if err:
        return err, code

    company = Company.query.get_or_404(id)
    company.approval_status = 'rejected'
    db.session.commit()
    cache.delete('admin_dashboard')
    return jsonify({'message': 'Company rejected'}), 200


@admin_bp.route('/companies/<int:id>/blacklist', methods=['PATCH'])
@jwt_required()
def blacklist_company(id):
    _, err, code = admin_required()
    if err:
        return err, code

    company = Company.query.get_or_404(id)
    data = request.get_json() or {}

    company.user.is_blacklisted = data.get('is_blacklisted', True)
    company.user.is_active = not company.user.is_blacklisted
    db.session.commit()

    status = 'blacklisted' if company.user.is_blacklisted else 'reactivated'
    return jsonify({'message': f'Company {status} successfully'}), 200


# Placement Drives 
@admin_bp.route('/drives', methods=['GET'])
@jwt_required()
def get_drives():
    _, err, code = admin_required()
    if err:
        return err, code

    drives = PlacementDrive.query.options(joinedload(PlacementDrive.company)).all()
    result = []
    for d in drives:
        data = d.to_dict()
        data['company_name'] = d.company.company_name
        result.append(data)
    return jsonify(result), 200


@admin_bp.route('/drives/<int:id>/approve', methods=['PATCH'])
@jwt_required()
def approve_drive(id):
    _, err, code = admin_required()
    if err:
        return err, code

    drive = PlacementDrive.query.get_or_404(id)
    drive.status = 'approved'
    db.session.commit()
    cache.delete('admin_dashboard')
    return jsonify({'message': 'Drive approved successfully'}), 200


@admin_bp.route('/drives/<int:id>/reject', methods=['PATCH'])
@jwt_required()
def reject_drive(id):
    _, err, code = admin_required()
    if err:
        return err, code

    drive = PlacementDrive.query.get_or_404(id)
    drive.status = 'rejected'
    db.session.commit()
    cache.delete('admin_dashboard')
    return jsonify({'message': 'Drive rejected'}), 200


@admin_bp.route('/drives/<int:id>/close', methods=['PATCH'])
@jwt_required()
def close_drive(id):
    _, err, code = admin_required()
    if err:
        return err, code

    drive = PlacementDrive.query.get_or_404(id)
    drive.status = 'closed'
    db.session.commit()
    cache.delete('admin_dashboard')
    return jsonify({'message': 'Drive marked as complete'}), 200


# Applications (all, across every drive)
# Eager-load student + drive + company in one query to avoid N+1.
@admin_bp.route('/applications', methods=['GET'])
@jwt_required()
def get_applications():
    _, err, code = admin_required()
    if err:
        return err, code

    applications = (
        Application.query
        .options(
            joinedload(Application.student),
            joinedload(Application.drive).joinedload(PlacementDrive.company),
        )
        .all()
    )
    result = []
    for a in applications:
        data = a.to_dict()
        data['student_name'] = a.student.full_name
        data['drive_title'] = a.drive.job_title
        data['company_name'] = a.drive.company.company_name
        result.append(data)
    return jsonify(result), 200


# Search (students and/or companies by keyword)
@admin_bp.route('/search', methods=['GET'])
@jwt_required()
def search():
    _, err, code = admin_required()
    if err:
        return err, code

    q = request.args.get('q', '').lower()
    search_type = request.args.get('type', 'all')
    like = f'%{q}%'

    students, companies = [], []

    if search_type in ('all', 'students'):
        student_list = Student.query.join(User).filter(
            db.or_(
                Student.full_name.ilike(like),
                Student.roll_number.ilike(like),
                Student.branch.ilike(like),
                User.email.ilike(like),
            )
        ).all()
        students = [s.to_dict() for s in student_list]

    if search_type in ('all', 'companies'):
        company_list = Company.query.join(User).filter(
            db.or_(
                Company.company_name.ilike(like),
                Company.industry.ilike(like),
                Company.hr_name.ilike(like),
                User.email.ilike(like),
            )
        ).all()
        companies = [c.to_dict() for c in company_list]

    return jsonify({'students': students, 'companies': companies}), 200


# Monthly Report Stats (current month's aggregate numbers)
@admin_bp.route('/reports/monthly', methods=['GET'])
@jwt_required()
def monthly_report():
    _, err, code = admin_required()
    if err:
        return err, code

    now = datetime.now(timezone.utc)

    drives = PlacementDrive.query.filter(
        db.extract('month', PlacementDrive.created_at) == now.month,
        db.extract('year', PlacementDrive.created_at) == now.year,
    ).count()

    applications = Application.query.filter(
        db.extract('month', Application.application_date) == now.month,
        db.extract('year', Application.application_date) == now.year,
    ).count()

    selected = Application.query.filter(
        Application.status == 'selected',
        db.extract('month', Application.updated_at) == now.month,
        db.extract('year', Application.updated_at) == now.year,
    ).count()

    return jsonify({
        'month': now.strftime('%B %Y'),
        'drives_conducted': drives,
        'total_applications': applications,
        'students_selected': selected,
    }), 200
