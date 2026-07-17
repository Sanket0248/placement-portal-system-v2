"""
routes/student.py — Student blueprint.

All endpoints require a valid JWT from a student-role user (except resume
serving and export download, which are public/unauthenticated).
Prefix: /api/student (set in app.py).

Endpoints:
  GET    /profile             — get student profile
  PUT    /profile             — update profile fields
  POST   /profile/resume      — upload a PDF resume (max 5 MB)
  GET    /dashboard           — overview: eligible drives, applications, stats
  GET    /drives              — browse approved drives (with eligibility + search)
  GET    /drives/<id>         — single drive detail
  POST   /drives/<id>/apply   — submit an application
  GET    /applications        — list my applications
  GET    /applications/<id>   — single application detail
  GET    /history             — placement history (all apps with job_type)
  POST   /export/csv          — trigger async CSV export (Celery task)
  GET    /export/status/<id>  — poll export task status
  GET    /export/download/<id>— download completed CSV
  GET    /resume/<filename>   — serve an uploaded resume file
"""

import os
from datetime import date

from flask import Blueprint, request, jsonify, current_app, send_from_directory
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy.orm import joinedload
from werkzeug.utils import secure_filename

from extensions import db
from models import User, Student, PlacementDrive, Application

student_bp = Blueprint('student', __name__)


# ── Helper: get the logged-in student user + profile ────────────
def get_current_student():
    """
    Verify the JWT user is a student and return (user, student, None, None).
    Returns (None, None, error_response, status_code) on failure.
    """
    user = db.session.get(User, get_jwt_identity())
    if not user or user.role != 'student':
        return None, None, jsonify({'error': 'Student access required'}), 403
    if not user.student_profile:
        return None, None, jsonify({'error': 'Student profile not found'}), 404
    return user, user.student_profile, None, None


# ── Helper: check if a student meets a drive's eligibility criteria ──
def _is_eligible(student, drive):
    """A student is eligible if their branch, CGPA, and year all match."""
    return (
        student.branch in drive.eligible_branches.split(',')
        and student.cgpa >= drive.min_cgpa
        and student.year_of_study == drive.eligible_year
    )


@student_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user, student, err, code = get_current_student()
    if err:
        return err, code
    data = student.to_dict()
    data['email'] = user.email
    return jsonify(data), 200


@student_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    _, student, err, code = get_current_student()
    if err:
        return err, code

    data = request.get_json() or {}
    student.full_name = data.get('full_name', student.full_name)
    student.phone = data.get('phone', student.phone)
    student.branch = data.get('branch', student.branch)
    student.cgpa = float(data.get('cgpa', student.cgpa))
    student.year_of_study = int(data.get('year_of_study', student.year_of_study))
    db.session.commit()
    return jsonify({'message': 'Profile updated successfully'}), 200


@student_bp.route('/profile/resume', methods=['POST'])
@jwt_required()
def upload_resume():
    _, student, err, code = get_current_student()
    if err:
        return err, code

    if 'resume' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['resume']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'error': 'Only PDF files are allowed'}), 400

    filename = secure_filename(f"resume_student_{student.id}.pdf")
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    student.resume_path = filename
    db.session.commit()
    return jsonify({'message': 'Resume uploaded successfully', 'filename': filename}), 200


@student_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    _, student, err, code = get_current_student()
    if err:
        return err, code

    all_drives = PlacementDrive.query.filter_by(status='approved').all()
    eligible_drives = [
        d.to_dict() for d in all_drives
        if _is_eligible(student, d) and d.application_deadline >= date.today()
    ]

    applications = (
        Application.query
        .options(joinedload(Application.drive).joinedload(PlacementDrive.company))
        .filter_by(student_id=student.id)
        .all()
    )
    app_data = []
    for a in applications:
        data = a.to_dict()
        data['job_title'] = a.drive.job_title
        data['company_name'] = a.drive.company.company_name
        app_data.append(data)

    return jsonify({
        'student': student.to_dict(),
        'eligible_drives': eligible_drives,
        'my_applications': app_data,
        'total_applied': len(applications),
        'shortlisted': sum(1 for a in applications if a.status == 'shortlisted'),
        'selected': sum(1 for a in applications if a.status == 'selected'),
    }), 200


@student_bp.route('/drives', methods=['GET'])
@jwt_required()
def get_drives():
    _, student, err, code = get_current_student()
    if err:
        return err, code

    search = request.args.get('search', '').lower()
    filter_eligible = request.args.get('eligible_only', 'false').lower() == 'true'

    drives = (
        PlacementDrive.query
        .options(joinedload(PlacementDrive.company))
        .filter_by(status='approved')
        .all()
    )

    # N+1 fix: fetch ALL of this student's applications in one query,
    # then look them up by drive_id in a dict. The original code ran a
    # separate query per drive to check if the student had already applied.
    my_apps = {a.drive_id: a for a in Application.query.filter_by(student_id=student.id).all()}

    result = []
    for d in drives:
        if search and search not in d.job_title.lower() and search not in d.company.company_name.lower():
            continue

        is_eligible = _is_eligible(student, d)
        if filter_eligible and not is_eligible:
            continue

        data = d.to_dict()
        data['company_name'] = d.company.company_name
        data['is_eligible'] = is_eligible
        existing = my_apps.get(d.id)
        data['already_applied'] = existing is not None
        data['application_status'] = existing.status if existing else None
        result.append(data)

    return jsonify(result), 200


@student_bp.route('/drives/<int:id>', methods=['GET'])
@jwt_required()
def get_drive(id):
    _, student, err, code = get_current_student()
    if err:
        return err, code

    drive = PlacementDrive.query.filter_by(id=id, status='approved').first_or_404()
    data = drive.to_dict()
    data['company_name'] = drive.company.company_name

    existing = Application.query.filter_by(student_id=student.id, drive_id=id).first()
    data['already_applied'] = existing is not None
    data['application_status'] = existing.status if existing else None
    return jsonify(data), 200


@student_bp.route('/drives/<int:id>/apply', methods=['POST'])
@jwt_required()
def apply_drive(id):
    _, student, err, code = get_current_student()
    if err:
        return err, code

    drive = PlacementDrive.query.filter_by(id=id, status='approved').first_or_404()

    if drive.application_deadline < date.today():
        return jsonify({'error': 'Application deadline has passed'}), 400

    if student.branch not in drive.eligible_branches.split(','):
        return jsonify({'error': 'Your branch is not eligible for this drive'}), 403
    if student.cgpa < drive.min_cgpa:
        return jsonify({'error': f'Minimum CGPA required is {drive.min_cgpa}'}), 403
    if student.year_of_study != drive.eligible_year:
        return jsonify({'error': f'Only year {drive.eligible_year} students can apply'}), 403

    if Application.query.filter_by(student_id=student.id, drive_id=id).first():
        return jsonify({'error': 'You have already applied to this drive'}), 409

    application = Application(
        student_id=student.id,
        drive_id=id,
        resume_snapshot=student.resume_path,
        status='applied',
    )
    db.session.add(application)
    db.session.commit()
    return jsonify({'message': 'Application submitted successfully!'}), 201


# ── Helper: serialize a student's applications with eager loading ─
def _serialize_applications(student_id, extra_fields=()):
    applications = (
        Application.query
        .options(joinedload(Application.drive).joinedload(PlacementDrive.company))
        .filter_by(student_id=student_id)
        .all()
    )
    result = []
    for a in applications:
        data = a.to_dict()
        data['job_title'] = a.drive.job_title
        data['company_name'] = a.drive.company.company_name
        data['package_lpa'] = a.drive.package_lpa
        for field in extra_fields:
            data[field] = getattr(a.drive, field)
        result.append(data)
    return result


@student_bp.route('/applications', methods=['GET'])
@jwt_required()
def get_applications():
    _, student, err, code = get_current_student()
    if err:
        return err, code
    return jsonify(_serialize_applications(student.id)), 200


@student_bp.route('/applications/<int:id>', methods=['GET'])
@jwt_required()
def get_application(id):
    _, student, err, code = get_current_student()
    if err:
        return err, code

    application = Application.query.filter_by(id=id, student_id=student.id).first_or_404()
    data = application.to_dict()
    data['job_title'] = application.drive.job_title
    data['company_name'] = application.drive.company.company_name
    data['job_description'] = application.drive.job_description
    data['package_lpa'] = application.drive.package_lpa
    return jsonify(data), 200


@student_bp.route('/history', methods=['GET'])
@jwt_required()
def placement_history():
    _, student, err, code = get_current_student()
    if err:
        return err, code
    return jsonify(_serialize_applications(student.id, extra_fields=('job_type',))), 200


@student_bp.route('/export/csv', methods=['POST'])
@jwt_required()
def export_csv():
    _, student, err, code = get_current_student()
    if err:
        return err, code

    from tasks.exports import export_applications_csv
    task = export_applications_csv.delay(student.id)
    return jsonify({'message': 'CSV export started', 'task_id': task.id}), 202


@student_bp.route('/resume/<path:filename>', methods=['GET'])
def serve_resume(filename):
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], secure_filename(filename))


@student_bp.route('/export/status/<task_id>', methods=['GET'])
@jwt_required()
def export_status(task_id):
    from celery.result import AsyncResult
    from app import celery
    task = AsyncResult(task_id, app=celery)
    if task.state == 'SUCCESS':
        return jsonify({'status': 'done', 'result': task.result}), 200
    if task.state == 'FAILURE':
        return jsonify({'status': 'failed'}), 200
    return jsonify({'status': 'pending'}), 200


@student_bp.route('/export/download/<task_id>', methods=['GET'])
def export_download(task_id):
    from celery.result import AsyncResult
    from app import celery
    task = AsyncResult(task_id, app=celery)
    if task.state == 'SUCCESS' and task.result.get('filename'):
        return send_from_directory(
            current_app.config['UPLOAD_FOLDER'],
            secure_filename(task.result['filename']),
            as_attachment=True,
        )
    return jsonify({'error': 'Export not ready'}), 404
