"""
tasks/reports.py — Monthly placement summary report email.

Runs on the 1st of every month at 9:00 AM (configured in celery_app.py).
Sends an HTML email to the admin showing this month's drives, total
applications, and students selected.
"""

from datetime import datetime, timezone

from celery import current_app as celery_app


@celery_app.task(name='tasks.reports.send_monthly_report')
def send_monthly_report():
    """Compile this month's stats and email them to the admin."""
    from flask_mail import Message
    from sqlalchemy.orm import joinedload

    from extensions import mail, db
    from models import User, PlacementDrive, Application

    now = datetime.now(timezone.utc)

    drives = (
        PlacementDrive.query
        .options(joinedload(PlacementDrive.company))
        .filter(
            db.extract('month', PlacementDrive.created_at) == now.month,
            db.extract('year', PlacementDrive.created_at) == now.year,
        )
        .all()
    )

    applications = Application.query.filter(
        db.extract('month', Application.application_date) == now.month,
        db.extract('year', Application.application_date) == now.year,
    ).all()

    selected = [a for a in applications if a.status == 'selected']

    drive_rows = "".join(
        f"<tr><td>{d.job_title}</td><td>{d.company.company_name}</td>"
        f"<td>{d.application_deadline}</td><td>{d.status}</td></tr>"
        for d in drives
    )

    html_report = f"""
    <html><body style="font-family: Arial; padding: 20px;">
        <h2 style="color:#1E3A5F;">Monthly Placement Report — {now.strftime('%B %Y')}</h2>
        <hr/>
        <h3>Summary</h3>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;">
            <tr style="background:#1E3A5F;color:white;"><th>Metric</th><th>Count</th></tr>
            <tr><td>Drives Conducted</td><td>{len(drives)}</td></tr>
            <tr><td>Total Applications</td><td>{len(applications)}</td></tr>
            <tr><td>Students Selected</td><td>{len(selected)}</td></tr>
        </table>
        <h3 style="margin-top:30px;">Drive Details</h3>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;width:100%;">
            <tr style="background:#1E3A5F;color:white;">
                <th>Job Title</th><th>Company</th><th>Deadline</th><th>Status</th>
            </tr>
            {drive_rows or '<tr><td colspan="4">No drives this month</td></tr>'}
        </table>
        <p style="color:#777;margin-top:20px;">Generated on {now.strftime('%d %B %Y')}</p>
    </body></html>
    """

    admin = User.query.filter_by(role='admin').first()
    if not admin:
        return 'Admin not found'

    try:
        msg = Message(
            subject=f"Monthly Placement Report — {now.strftime('%B %Y')}",
            recipients=[admin.email],
            html=html_report,
        )
        mail.send(msg)
        return f"Report sent to {admin.email}"
    except Exception as e:
        return f"Error: {e}"
