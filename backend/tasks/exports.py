"""
tasks/exports.py — Async CSV export of a student's applications.

Triggered when a student clicks "Export CSV" on their dashboard.
The frontend polls /api/student/export/status/<task_id> until the
task finishes, then fetches the file via /api/student/export/download/<task_id>.

bind=True gives the task access to self.request.id (used in the filename).
"""

import csv
import os

from celery import current_app as celery_app


@celery_app.task(name='tasks.exports.export_applications_csv', bind=True)
def export_applications_csv(self, student_id):
    """Generate a CSV file with all of a student's applications and return the filename."""
    from sqlalchemy.orm import joinedload

    from models import Application, Student, PlacementDrive

    student = Student.query.get(student_id)
    if not student:
        return {'status': 'error', 'message': 'Student not found'}

    applications = (
        Application.query
        .options(joinedload(Application.drive).joinedload(PlacementDrive.company))
        .filter_by(student_id=student_id)
        .all()
    )

    upload_folder = os.path.join(os.path.dirname(__file__), '..', 'uploads')
    os.makedirs(upload_folder, exist_ok=True)

    filename = f"export_student_{student_id}_{self.request.id}.csv"
    filepath = os.path.join(upload_folder, filename)

    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'Application ID', 'Student ID', 'Student Name', 'Company Name',
            'Drive Title', 'Job Type', 'Package (LPA)', 'Application Date',
            'Status', 'Updated At',
        ])
        for a in applications:
            writer.writerow([
                a.id, a.student_id, student.full_name,
                a.drive.company.company_name, a.drive.job_title, a.drive.job_type,
                a.drive.package_lpa, a.application_date, a.status, a.updated_at,
            ])

    return {
        'status': 'done',
        'filename': filename,
        'message': f'{len(applications)} records exported.',
    }
