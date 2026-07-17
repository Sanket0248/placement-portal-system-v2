"""
config.py — Central configuration for the Flask application.

All sensitive values (passwords, API keys, secret keys) are read from
environment variables, which are loaded from a local .env file by
python-dotenv. This keeps secrets out of version control.

The Config class is passed to Flask via app.config.from_object(Config).
"""

import os

# Absolute path to this file's directory (the backend/ folder).
# Used as a reference point for building paths to instance/, uploads/, etc.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _bool(value, default=False):
    """Convert an environment variable string like 'true' / '1' to a Python bool."""
    if value is None:
        return default
    return str(value).strip().lower() in ('1', 'true', 'yes', 'on')


class Config:
    """All configuration settings, grouped by subsystem."""

    # Flask core
    # SECRET_KEY is used by Flask for session signing and CSRF protection.
    # JWT_SECRET_KEY is used by Flask-JWT-Extended to sign JSON Web Tokens.
    # Both should be long random strings in production.
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-only-change-me')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-only-change-me')

    # Database (SQLAlchemy) 
    # Defaults to a local SQLite file at backend/instance/placement.db.
    # In production you could point this to PostgreSQL / MySQL.
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'sqlite:///' + os.path.join(BASE_DIR, 'instance', 'placement.db'),
    )
    # Disable the legacy event system that wastes memory.
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Cache (Flask-Caching) 
    # We use Redis for caching API responses (e.g. admin dashboard stats).
    # Set CACHE_TYPE=SimpleCache in dev if you don't have Redis running.
    CACHE_TYPE = os.getenv('CACHE_TYPE', 'redis')
    CACHE_REDIS_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0')
    CACHE_DEFAULT_TIMEOUT = int(os.getenv('CACHE_DEFAULT_TIMEOUT', '300'))  # seconds

    # Celery (async task queue)
    # Celery uses the same Redis instance as its message broker and
    # result backend (stores task return values so we can poll status).
    CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0')
    CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0')

    # Email (Flask-Mail via Gmail SMTP)
    # Use a Google "App Password" (not your login password) for MAIL_PASSWORD.
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.getenv('MAIL_PORT', '587'))
    MAIL_USE_TLS = _bool(os.getenv('MAIL_USE_TLS'), True)
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER') or os.getenv('MAIL_USERNAME')

    # Seed admin account
    # On first run, if no admin user exists in the DB, one is created
    # with these credentials. Change them in .env before deploying.
    ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', 'admin@placement.local')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

    # File uploads
    # Resumes and CSV exports are saved here. Flask enforces the size limit.
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB max upload

    # Public URL (used in outgoing emails)
    # Links inside interview-scheduled / result emails point here.
    APP_BASE_URL = os.getenv('APP_BASE_URL', 'http://127.0.0.1:5000')
