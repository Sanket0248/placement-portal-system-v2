"""
routes/company.py — Company (recruiter) blueprint.

All endpoints require a valid JWT from a company-role user.
Prefix: /api/company (set in app.py).

Endpoints:
  GET    /profile                       — get company profile
  PUT    /profile                       — update company profile fields
  GET    /dashboard                     — overview stats + drives with applicant counts
  GET    /drives                        — list this company's drives
  POST   /drives                        — create a new drive (pending admin approval)
  GET    /drives/<id>                   — single drive detail
  PUT    /drives/<id>                   — edit a pending drive
  DELETE /drives/<id>                   — delete a pending drive
  PATCH  /drives/<id>/close             — mark an approved drive as complete
  GET    /drives/<id>/applications      — list applicants for a drive
  PATCH  /applications/<id>/status      — update an application's status
  POST   /applications/<id>/interview   — schedule or reschedule an interview
  PATCH  /applications/<id>/interview/result — set interview result (passed/failed)
"""

from datetime import date, datetime

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from sqlalchemy.orm import joinedload

from extensions import db, mail
from models import User, Company, PlacementDrive, Application, Interview

company_bp = Blueprint('company', __name__)


# ── Helper: get the logged-in company user + profile ────────────
def get_current_company():
    """
    Verify the JWT user is a company and return (user, company, None, None).
    Returns (None, None, error_response, status_code) on failure.
    """
    user = db.session.get(User, get_jwt_identity())
    if not user or user.role != 'company':
        return None, None, jsonify({'error': 'Company access required'}), 403
    if not user.company_profile:
        return None, None, jsonify({'error': 'Company profile not found'}), 404
    return user, user.company_profile, None, None


# ── Helper: aggregate application counts in one query ───────────
def _application_counts(company_id):
    """
    Single SQL query that returns {drive_id: {status: count}} for ALL
    of a company's drives. This replaces the original code which ran
    a separate COUNT query per drive per status (N+1 problem).
    """
    rows = (
        db.session.query(Application.drive_id, Application.status, func.count(Application.id))
        .join(PlacementDrive, Application.drive_id == PlacementDrive.id)
        .filter(PlacementDrive.company_id == company_id)
        .group_by(Application.drive_id, Application.status)
        .all()
    )
    counts = {}
    for drive_id, status, n in rows:
        counts.setdefault(drive_id, {})[status] = n
    return counts


@company_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    _, company, err, code = get_current_company()
    if err:
        return err, code
    return jsonify(company.to_dict()), 200


@company_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    _, company, err, code = get_current_company()
    if err:
        return err, code

    data = request.get_json() or {}
    company.hr_name = data.get('hr_name', company.hr_name)
    company.hr_email = data.get('hr_email', company.hr_email)
    company.website = data.get('website', company.website)
    company.industry = data.get('industry', company.industry)
    company.description = data.get('description', company.description)
    db.session.commit()
    return jsonify({'message': 'Profile updated successfully'}), 200


@company_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    _, company, err, code = get_current_company()
    if err:
        return err, code

    drives = PlacementDrive.query.filter_by(company_id=company.id).all()
    counts = _application_counts(company.id)

    drive_data = []
    for d in drives:
        info = d.to_dict()
        c = counts.get(d.id, {})
        info['total_applicants'] = sum(c.values())
        info['shortlisted'] = c.get('shortlisted', 0)
        info['selected'] = c.get('selected', 0)
        drive_data.append(info)

    return jsonify({
        'company': company.to_dict(),
        'approval_status': company.approval_status,
        'total_drives': len(drives),
        'drives': drive_data,
    }), 200


@company_bp.route('/drives', methods=['GET'])
@jwt_required()
def get_drives():
    _, company, err, code = get_current_company()
    if err:
        return err, code

    drives = PlacementDrive.query.filter_by(company_id=company.id).all()
    counts = _application_counts(company.id)

    result = []
    for d in drives:
        info = d.to_dict()
        info['total_applicants'] = sum(counts.get(d.id, {}).values())
        result.append(info)
    return jsonify(result), 200


@company_bp.route('/drives', methods=['POST'])
@jwt_required()
def create_drive():
    _, company, err, code = get_current_company()
    if err:
        return err, code

    if company.approval_status != 'approved':
        return jsonify({'error': 'Your company must be approved by admin before creating drives'}), 403

    data = request.get_json() or {}
    required = ['job_title', 'job_description', 'eligible_branches', 'min_cgpa', 'eligible_year', 'application_deadline']
    for field in required:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400

    branches = data['eligible_branches']
    if isinstance(branches, list):
        branches = ','.join(branches)

    drive = PlacementDrive(
        company_id=company.id,
        job_title=data['job_title'],
        job_description=data['job_description'],
        eligible_branches=branches,
        min_cgpa=float(data['min_cgpa']),
        eligible_year=int(data['eligible_year']),
        application_deadline=date.fromisoformat(data['application_deadline']),
        job_type=data.get('job_type', 'Full-time'),
        package_lpa=float(data.get('package_lpa', 0)),
        status='pending',
    )
    db.session.add(drive)
    db.session.commit()

    return jsonify({'message': 'Drive created successfully. Awaiting admin approval.', 'drive': drive.to_dict()}), 201


@company_bp.route('/drives/<int:id>', methods=['GET'])
@jwt_required()
def get_drive(id):
    _, company, err, code = get_current_company()
    if err:
        return err, code

    drive = PlacementDrive.query.filter_by(id=id, company_id=company.id).first_or_404()
    return jsonify(drive.to_dict()), 200


@company_bp.route('/drives/<int:id>', methods=['PUT'])
@jwt_required()
def update_drive(id):
    _, company, err, code = get_current_company()
    if err:
        return err, code

    drive = PlacementDrive.query.filter_by(id=id, company_id=company.id).first_or_404()
    if drive.status == 'approved':
        return jsonify({'error': 'Cannot edit an approved drive'}), 403

    data = request.get_json() or {}
    drive.job_title = data.get('job_title', drive.job_title)
    drive.job_description = data.get('job_description', drive.job_description)
    drive.min_cgpa = float(data.get('min_cgpa', drive.min_cgpa))
    drive.eligible_year = int(data.get('eligible_year', drive.eligible_year))
    drive.job_type = data.get('job_type', drive.job_type)
    drive.package_lpa = float(data.get('package_lpa', drive.package_lpa))

    if 'eligible_branches' in data:
        branches = data['eligible_branches']
        if isinstance(branches, list):
            branches = ','.join(branches)
        drive.eligible_branches = branches

    if 'application_deadline' in data:
        drive.application_deadline = date.fromisoformat(data['application_deadline'])

    db.session.commit()
    return jsonify({'message': 'Drive updated successfully'}), 200


@company_bp.route('/drives/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_drive(id):
    _, company, err, code = get_current_company()
    if err:
        return err, code

    drive = PlacementDrive.query.filter_by(id=id, company_id=company.id).first_or_404()
    if drive.status == 'approved':
        return jsonify({'error': 'Cannot delete an approved drive'}), 403

    db.session.delete(drive)
    db.session.commit()
    return jsonify({'message': 'Drive deleted successfully'}), 200


@company_bp.route('/drives/<int:id>/close', methods=['PATCH'])
@jwt_required()
def close_drive(id):
    _, company, err, code = get_current_company()
    if err:
        return err, code

    drive = PlacementDrive.query.filter_by(id=id, company_id=company.id).first_or_404()
    if drive.status != 'approved':
        return jsonify({'error': 'Only approved drives can be closed'}), 403

    drive.status = 'closed'
    db.session.commit()
    return jsonify({'message': 'Drive marked as complete'}), 200


@company_bp.route('/drives/<int:id>/applications', methods=['GET'])
@jwt_required()
def get_drive_applications(id):
    _, company, err, code = get_current_company()
    if err:
        return err, code

    drive = PlacementDrive.query.filter_by(id=id, company_id=company.id).first_or_404()
    applications = (
        Application.query
        .options(joinedload(Application.student))
        .filter_by(drive_id=drive.id)
        .all()
    )

    result = []
    for a in applications:
        data = a.to_dict()
        data['student_name'] = a.student.full_name
        data['roll_number'] = a.student.roll_number
        data['branch'] = a.student.branch
        data['cgpa'] = a.student.cgpa
        data['resume_path'] = a.student.resume_path
        result.append(data)
    return jsonify(result), 200


# ── Helper: ensure the company owns this application ────────────
def _owned_application_or_error(app_id, company):
    """
    Fetch an application by ID, but only if it belongs to one of this
    company's drives. Prevents a company from modifying another company's applicants.
    Returns (application, None) on success, or (None, (error_response, code)) on failure.
    """
    application = db.session.get(Application, app_id)
    if not application:
        return None, (jsonify({'error': 'Application not found'}), 404)
    drive = PlacementDrive.query.filter_by(id=application.drive_id, company_id=company.id).first()
    if not drive:
        return None, (jsonify({'error': 'Unauthorized'}), 403)
    return application, None


@company_bp.route('/applications/<int:id>/status', methods=['PATCH'])
@jwt_required()
def update_application_status(id):
    _, company, err, code = get_current_company()
    if err:
        return err, code

    application, error = _owned_application_or_error(id, company)
    if error:
        return error

    new_status = (request.get_json() or {}).get('status')
    valid_statuses = ['applied', 'shortlisted', 'selected', 'rejected']
    if new_status not in valid_statuses:
        return jsonify({'error': f'Invalid status. Must be one of {valid_statuses}'}), 400

    application.status = new_status
    db.session.commit()
    return jsonify({'message': f'Application status updated to {new_status}'}), 200


@company_bp.route('/applications/<int:id>/interview', methods=['POST'])
@jwt_required()
def schedule_interview(id):
    _, company, err, code = get_current_company()
    if err:
        return err, code

    application, error = _owned_application_or_error(id, company)
    if error:
        return error

    data = request.get_json() or {}
    if not data.get('scheduled_at'):
        return jsonify({'error': 'scheduled_at is required'}), 400

    is_reschedule = bool(application.interview)

    if is_reschedule:
        interview = application.interview
        interview.scheduled_at = datetime.fromisoformat(data['scheduled_at'])
        interview.mode = data.get('mode', interview.mode)
        interview.location = data.get('location', interview.location)
        interview.notes = data.get('notes', interview.notes)
    else:
        interview = Interview(
            application_id=id,
            scheduled_at=datetime.fromisoformat(data['scheduled_at']),
            mode=data.get('mode', 'Online'),
            location=data.get('location', ''),
            notes=data.get('notes', ''),
        )
        db.session.add(interview)

    if application.status == 'applied':
        application.status = 'shortlisted'

    db.session.commit()

    _send_interview_scheduled_email(application, interview, company, is_reschedule)

    msg = 'Interview rescheduled successfully' if is_reschedule else 'Interview scheduled successfully'
    return jsonify({'message': msg}), 200


@company_bp.route('/applications/<int:id>/interview/result', methods=['PATCH'])
@jwt_required()
def update_interview_result(id):
    _, company, err, code = get_current_company()
    if err:
        return err, code

    application, error = _owned_application_or_error(id, company)
    if error:
        return error

    if not application.interview:
        return jsonify({'error': 'No interview scheduled yet'}), 404

    result = (request.get_json() or {}).get('result')
    if result not in ['pending', 'passed', 'failed']:
        return jsonify({'error': 'Invalid result'}), 400

    application.interview.result = result
    if result == 'passed':
        application.status = 'selected'
    elif result == 'failed':
        application.status = 'rejected'

    db.session.commit()
    _send_interview_result_email(application, company)
    return jsonify({'message': 'Interview result updated'}), 200


# ── Email helpers ────────────────────────────────────────────────
# These send HTML emails to students when interviews are scheduled,
# rescheduled, or when interview results (passed/failed) are set.
# Emails use APP_BASE_URL from config for the dashboard link.
def _dashboard_link():
    return f"{current_app.config['APP_BASE_URL']}/#/student/dashboard"


def _send_interview_scheduled_email(application, interview, company, is_reschedule=False):
    """Send interview scheduled / rescheduled email to the student."""
    try:
        from flask_mail import Message

        student = application.student
        drive = application.drive
        action = 'Rescheduled' if is_reschedule else 'Scheduled'
        subject_emoji = '🔄' if is_reschedule else '📅'
        scheduled_str = interview.scheduled_at.strftime('%A, %d %B %Y at %I:%M %p')

        location_row = ''
        if interview.location:
            location_row = f"""
            <tr>
              <td style="padding:10px 16px;color:#6b7280;font-weight:500;width:140px;">Location</td>
              <td style="padding:10px 16px;">{interview.location}</td>
            </tr>"""

        notes_row = ''
        if interview.notes:
            notes_row = f"""
            <tr style="background:#f9fafb;">
              <td style="padding:10px 16px;color:#6b7280;font-weight:500;">Notes</td>
              <td style="padding:10px 16px;">{interview.notes}</td>
            </tr>"""

        reschedule_banner = ''
        if is_reschedule:
            reschedule_banner = """
            <div style="background:#fff3cd;border:1px solid #ffc107;border-radius:8px;
                        padding:12px 16px;margin-bottom:20px;">
              <strong>🔄 Your interview has been rescheduled.</strong>
              Please note the updated date and time below.
            </div>"""

        html_body = f"""
        <html><body style="font-family:Arial,sans-serif;background:#f0f4f8;padding:24px;margin:0;">
          <div style="max-width:600px;margin:auto;background:white;border-radius:12px;
                      overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,0.1);">
            <div style="background:#1E3A5F;padding:24px 28px;">
              <h2 style="color:white;margin:0;font-size:20px;">{subject_emoji} Interview {action}</h2>
              <p style="color:#a8c0d6;margin:6px 0 0;font-size:14px;">
                {company.company_name} — {drive.job_title}
              </p>
            </div>
            <div style="padding:28px;">
              <p style="font-size:16px;color:#2d3748;">Hi <strong>{student.full_name}</strong>,</p>
              {reschedule_banner}
              <p style="color:#4a5568;">
                Your interview for <strong>{drive.job_title}</strong> at
                <strong>{company.company_name}</strong> has been {action.lower()}.
              </p>
              <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;
                          overflow:hidden;margin:20px 0;">
                <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
                  <tr style="background:#1E3A5F;color:white;">
                    <td colspan="2" style="padding:12px 16px;font-weight:600;font-size:15px;">Interview Details</td>
                  </tr>
                  <tr>
                    <td style="padding:10px 16px;color:#6b7280;font-weight:500;width:140px;">Date &amp; Time</td>
                    <td style="padding:10px 16px;font-weight:600;color:#1E3A5F;">{scheduled_str}</td>
                  </tr>
                  <tr style="background:#f9fafb;">
                    <td style="padding:10px 16px;color:#6b7280;font-weight:500;">Mode</td>
                    <td style="padding:10px 16px;">{interview.mode}</td>
                  </tr>
                  {location_row}
                  {notes_row}
                  <tr>
                    <td style="padding:10px 16px;color:#6b7280;font-weight:500;">Package</td>
                    <td style="padding:10px 16px;">₹{drive.package_lpa} LPA</td>
                  </tr>
                </table>
              </div>
              <div style="margin-top:24px;text-align:center;">
                <a href="{_dashboard_link()}"
                   style="background:#1E3A5F;color:white;padding:12px 28px;text-decoration:none;
                          border-radius:8px;font-size:15px;display:inline-block;">
                  View My Applications &rarr;
                </a>
              </div>
              <p style="color:#a0aec0;font-size:12px;margin-top:28px;border-top:1px solid #f0f0f0;
                        padding-top:16px;text-align:center;">
                This is an automated notification from your Placement Portal.
              </p>
            </div>
          </div>
        </body></html>
        """

        msg = Message(
            subject=f"[Placement Portal] {subject_emoji} Interview {action} — {company.company_name} ({drive.job_title})",
            recipients=[student.user.email],
            html=html_body,
            body=(
                f"Hi {student.full_name},\n\n"
                f"Your interview for {drive.job_title} at {company.company_name} has been {action.lower()}.\n\n"
                f"Date & Time : {scheduled_str}\n"
                f"Mode        : {interview.mode}\n"
                f"Location    : {interview.location or 'N/A'}\n"
                f"Notes       : {interview.notes or 'None'}\n\n"
                f"Log in: {current_app.config['APP_BASE_URL']}\n\n— Placement Cell"
            ),
        )
        mail.send(msg)
    except Exception as e:
        print(f"Failed to send interview email: {e}")


def _send_interview_result_email(application, company):
    """Send interview result (selected / rejected) email to the student."""
    try:
        from flask_mail import Message

        student = application.student
        drive = application.drive
        result = application.interview.result

        if result == 'passed':
            status_color, status_emoji = '#27ae60', '🎉'
            status_text = 'Congratulations! You have been SELECTED'
            status_subtext = f"You passed the interview for <strong>{drive.job_title}</strong> at <strong>{company.company_name}</strong>."
            cta_text = 'You will be contacted by the company with further onboarding details.'
        elif result == 'failed':
            status_color, status_emoji = '#e74c3c', '📋'
            status_text = 'Interview Result — Not Selected'
            status_subtext = f"Unfortunately, you were not selected for <strong>{drive.job_title}</strong> at <strong>{company.company_name}</strong> this time."
            cta_text = "Keep applying to other drives — your next opportunity is around the corner."
        else:
            return

        html_body = f"""
        <html><body style="font-family:Arial,sans-serif;background:#f0f4f8;padding:24px;margin:0;">
          <div style="max-width:600px;margin:auto;background:white;border-radius:12px;
                      overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,0.1);">
            <div style="background:#1E3A5F;padding:24px 28px;">
              <h2 style="color:white;margin:0;font-size:20px;">{status_emoji} Interview Result</h2>
              <p style="color:#a8c0d6;margin:6px 0 0;font-size:14px;">{company.company_name} — {drive.job_title}</p>
            </div>
            <div style="padding:28px;">
              <p style="font-size:16px;color:#2d3748;">Hi <strong>{student.full_name}</strong>,</p>
              <div style="background:{status_color}15;border-left:4px solid {status_color};
                          border-radius:8px;padding:16px 20px;margin:20px 0;">
                <p style="color:{status_color};font-size:18px;font-weight:700;margin:0 0 6px;">
                  {status_emoji} {status_text}
                </p>
                <p style="color:#4a5568;margin:0;">{status_subtext}</p>
              </div>
              <p style="color:#4a5568;">{cta_text}</p>
              <div style="margin-top:24px;text-align:center;">
                <a href="{_dashboard_link()}"
                   style="background:#1E3A5F;color:white;padding:12px 28px;text-decoration:none;
                          border-radius:8px;font-size:15px;display:inline-block;">
                  View Placement History &rarr;
                </a>
              </div>
              <p style="color:#a0aec0;font-size:12px;margin-top:28px;border-top:1px solid #f0f0f0;
                        padding-top:16px;text-align:center;">
                This is an automated notification from your Placement Portal.
              </p>
            </div>
          </div>
        </body></html>
        """

        result_label = 'Selected 🎉' if result == 'passed' else 'Not Selected'
        msg = Message(
            subject=f"[Placement Portal] {status_emoji} Interview Result — {company.company_name}: {result_label}",
            recipients=[student.user.email],
            html=html_body,
            body=(
                f"Hi {student.full_name},\n\n"
                f"Your interview result for {drive.job_title} at {company.company_name}:\n\n"
                f"Result : {'SELECTED' if result == 'passed' else 'NOT SELECTED'}\n"
                f"Package: ₹{drive.package_lpa} LPA\n\n"
                f"Log in: {current_app.config['APP_BASE_URL']}\n\n— Placement Cell"
            ),
        )
        mail.send(msg)
    except Exception as e:
        print(f"Failed to send result email: {e}")
