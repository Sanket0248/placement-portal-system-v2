"""
extensions.py — Instantiate Flask extensions as module-level singletons.

Each extension is created here WITHOUT an app, then initialized with the
actual Flask app inside create_app() in app.py via ext.init_app(app).
This pattern (called the "application factory" pattern) avoids circular
imports and lets us access db, cache, etc. from any module.
"""

from flask_sqlalchemy import SQLAlchemy       # ORM for database access
from flask_caching import Cache               # Response caching (Redis-backed)
from flask_jwt_extended import JWTManager      # JWT authentication helpers
from flask_mail import Mail                    # Email sending (SMTP)
from flask_cors import CORS                    # Cross-Origin Resource Sharing headers

db = SQLAlchemy()   # Use as: db.session, db.Column, db.Model, etc.
cache = Cache()     # Use as: @cache.cached(timeout=300)
jwt = JWTManager()  # Use as: @jwt_required(), get_jwt_identity()
mail = Mail()       # Use as: mail.send(Message(...))
cors = CORS()       # Allows the Vue frontend (if served separately) to call the API
