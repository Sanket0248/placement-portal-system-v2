"""
tasks/reminders.py — Daily deadline reminder emails.

Runs every day at 8:00 AM (configured in celery_app.py beat_schedule).
Finds placement drives whose deadline is within 3 days, then emails
each eligible student a reminder listing those drives.
"""

from datetime import date, timedelta

from celery import current_app as celery_app


@celery_app.task(name='tasks.reminders.send_daily_reminders')
def send_daily_reminders():
    """Find drives with deadlines in ≤3 days and email eligible students."""
    from flask_mail import Message
    from sqlalchemy.orm import joinedload

    from extensions import mail
    from models import Student, PlacementDrive

    today = date.today()
    upcoming = (
        PlacementDrive.query
        .options(joinedload(PlacementDrive.company))
        .filter(
            PlacementDrive.status == 'approved',
            PlacementDrive.application_deadline >= today,
            PlacementDrive.application_deadline <= today + timedelta(days=3),
        )
        .all()
    )

    if not upcoming:
        return 'No reminders sent'

    students = Student.query.options(joinedload(Student.user)).all()
    sent = 0

    for student in students:
        eligible_drives = [
            d for d in upcoming
            if student.branch in d.eligible_branches.split(',')
            and student.cgpa >= d.min_cgpa
            and student.year_of_study == d.eligible_year
        ]
        if not eligible_drives:
            continue

        drive_list = "\n".join(
            f"- {d.job_title} at {d.company.company_name} (Deadline: {d.application_deadline})"
            for d in eligible_drives
        )

        try:
            msg = Message(
                subject='Placement Drive Deadline Reminder',
                recipients=[student.user.email],
                body=(
                    f"Hi {student.full_name},\n\n"
                    f"Upcoming deadlines:\n{drive_list}\n\n"
                    f"Log in to apply!\n\nPlacement Cell"
                ),
            )
            mail.send(msg)
            sent += 1
        except Exception as e:
            print(f"Failed to send to {student.user.email}: {e}")

    return f"Sent {sent} reminders"
