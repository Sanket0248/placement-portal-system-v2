"""
app.py — Application factory and entry point.

This file:
  1. Loads environment variables from .env (python-dotenv)
  2. Creates the Flask app and initializes all extensions
  3. Registers the four API blueprints (auth, admin, company, student)
  4. Sets up the single route that serves the Vue SPA shell
  5. Seeds the default admin account on first run
  6. Creates the Celery instance for background tasks

Run with:  python app.py
"""

import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

from flask import Flask, render_template
from werkzeug.security import generate_password_hash

from config import Config
from extensions import db, cache, jwt, mail, cors
from celery_app import make_celery

# Load .env file BEFORE reading Config, so os.getenv() picks up our secrets.


def create_app():
    """
    Application factory — builds and returns a configured Flask app.

    This pattern lets us create multiple app instances (e.g. for testing)
    and avoids import-time side effects.
    """
    # Point Flask at the separate frontend/ folder for serving static assets
    # and the HTML template. The frontend/ folder sits next to backend/.
    frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    app = Flask(
        __name__,
        static_folder=os.path.abspath(frontend_dir),   # serves CSS/JS from frontend/
        static_url_path='/static',                       # URL prefix: /static/css/styles.css
        template_folder=os.path.abspath(frontend_dir),  # Jinja looks for index.html here
    )

    # Pull all settings from config.py's Config class into app.config.
    app.config.from_object(Config)

    # Ensure the uploads/ and instance/ directories exist.
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), 'instance'), exist_ok=True)

    # ── Initialize extensions with this app ─────────────────────
    db.init_app(app)
    cache.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

    # ── Create database tables & seed admin ─────────────────────
    with app.app_context():
        import models  # noqa: F401  — importing registers models with SQLAlchemy
        db.create_all()      # Creates tables if they don't exist yet
        _seed_admin(app)     # Ensure at least one admin user exists

    # ── Register API blueprints (each handles one role's endpoints) ──
    from routes.auth import auth_bp
    from routes.admin import admin_bp
    from routes.company import company_bp
    from routes.student import student_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(company_bp, url_prefix='/api/company')
    app.register_blueprint(student_bp, url_prefix='/api/student')

    # ── SPA route ───────────────────────────────────────────────
    @app.route('/')
    def index():
        """
        Serve the single-page application shell.

        Vue Router (hash mode) handles all client-side routing, so the
        server only needs to return this one HTML page. CSS/JS assets are
        served automatically by Flask's built-in /static handler.
        """
        return render_template('index.html')

    return app


def _seed_admin(app):
    """
    Create the default admin user on first run.

    Credentials come from ADMIN_EMAIL and ADMIN_PASSWORD in .env.
    If an admin already exists, this does nothing.
    """
    from models import User

    if User.query.filter_by(role='admin').first():
        return  # Admin already exists — skip

    admin = User(
        email=app.config['ADMIN_EMAIL'],
        password_hash=generate_password_hash(app.config['ADMIN_PASSWORD']),
        role='admin',
        is_active=True,
        is_blacklisted=False,
    )
    db.session.add(admin)
    db.session.commit()
    print(f"Admin account created: {app.config['ADMIN_EMAIL']}")


# ── Create the app and Celery instances at module level ─────────
# These are used by:
#   - `python app.py` → runs the Flask dev server
#   - `celery -A app.celery worker` → runs the Celery worker
#   - `celery -A app.celery beat` → runs the Celery scheduler
flask_app = create_app()
celery = make_celery(flask_app)


if __name__ == '__main__':
    flask_app.run(debug=True)
