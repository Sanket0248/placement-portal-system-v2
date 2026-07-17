"""
celery_app.py — Create and configure the Celery instance.

Celery is a distributed task queue. We use it for three things:
  1. Daily email reminders about upcoming drive deadlines (tasks/reminders.py)
  2. Monthly placement report emails to admin (tasks/reports.py)
  3. Async CSV export of a student's applications (tasks/exports.py)

Celery needs a message broker (Redis) to communicate between the Flask
web process and the Celery worker process.
"""

from celery import Celery
from celery.schedules import crontab


def make_celery(app):
    """
    Factory that creates a Celery instance tied to the Flask app.

    The ContextTask wrapper ensures every Celery task runs inside a Flask
    application context, so it can access db, mail, config, etc.
    """
    celery = Celery(app.import_name)

    celery.conf.update(
        broker_url=app.config['CELERY_BROKER_URL'],
        result_backend=app.config['CELERY_RESULT_BACKEND'],

        # Retry connecting to Redis on startup instead of crashing immediately.
        broker_connection_retry_on_startup=True,
        broker_transport='redis',

        # Use Indian Standard Time for scheduling (for crontab triggers).
        timezone='Asia/Kolkata',

        # Tell Celery where to find our task functions.
        include=['tasks.reminders', 'tasks.reports', 'tasks.exports'],

        # Celery Beat schedule — periodic tasks that run automatically.
        beat_schedule={
            # Every day at 8:00 AM: remind students about deadlines in ≤3 days.
            'daily-reminders': {
                'task': 'tasks.reminders.send_daily_reminders',
                'schedule': crontab(hour=8, minute=0),
            },
            # 1st of every month at 9:00 AM: email admin a summary report.
            'monthly-report': {
                'task': 'tasks.reports.send_monthly_report',
                'schedule': crontab(day_of_month=1, hour=9, minute=0),
            },
        },
    )

    class ContextTask(celery.Task):
        """Wrap every task execution in Flask's app context."""
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
