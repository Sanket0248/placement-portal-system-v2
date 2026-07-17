"""
routes/auth.py — Authentication blueprint.

Handles user registration and login for all three roles.
All endpoints are prefixed with /api/auth (set in app.py).

Endpoints:
  POST /api/auth/register/student  — register a new student account
  POST /api/auth/register/company  — register a new company account (pending approval)
  POST /api/auth/login             — authenticate and receive a JWT token
  GET  /api/auth/me                — get current user info (requires valid token)
"""

from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from extensions import db
from models import User, Student, Company

auth_bp = Blueprint('auth', __name__)


def _profile_for(user):
    """Return the role-specific profile dict (student or company) for a user."""
    if user.role == 'student' and user.student_profile:
        return user.student_profile.to_dict()
    if user.role == 'company' and user.company_profile:
        return user.company_profile.to_dict()
    return None


# Student Registration
@auth_bp.route('/register/student', methods=['POST'])
def register_student():
    """
    Create a new student account.

    Expects JSON body with: email, password, full_name, roll_number,
    branch, cgpa, year_of_study (and optional phone).
    Creates both a User (for login) and a Student (for profile data).
    """
    data = request.get_json() or {}

    # Validate that all required fields are present.
    required = ['email', 'password', 'full_name', 'roll_number', 'branch', 'cgpa', 'year_of_study']
    for field in required:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400

    # Check for duplicate email or roll number.
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409

    if Student.query.filter_by(roll_number=data['roll_number']).first():
        return jsonify({'error': 'Roll number already registered'}), 409

    # Create the User record (handles login credentials).
    user = User(
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        role='student',
    )
    db.session.add(user)
    db.session.flush()  # flush() assigns user.id without committing yet

    # Create the Student profile linked to this user.
    student = Student(
        user_id=user.id,
        full_name=data['full_name'],
        roll_number=data['roll_number'],
        branch=data['branch'],
        cgpa=float(data['cgpa']),
        year_of_study=int(data['year_of_study']),
        phone=data.get('phone', ''),
    )
    db.session.add(student)
    db.session.commit()  # commit both User + Student together

    return jsonify({'message': 'Student registered successfully'}), 201


# Company Registration
@auth_bp.route('/register/company', methods=['POST'])
def register_company():
    """
    Create a new company account.

    The company starts with approval_status='pending'. An admin must
    approve it before the company can create placement drives.
    """
    data = request.get_json() or {}

    required = ['email', 'password', 'company_name', 'hr_name', 'hr_email']
    for field in required:
        if field not in data:
            return jsonify({'error': f'{field} is required'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409

    user = User(
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        role='company',
    )
    db.session.add(user)
    db.session.flush()

    company = Company(
        user_id=user.id,
        company_name=data['company_name'],
        hr_name=data['hr_name'],
        hr_email=data['hr_email'],
        website=data.get('website', ''),
        industry=data.get('industry', ''),
        description=data.get('description', ''),
        approval_status='pending',  # needs admin approval
    )
    db.session.add(company)
    db.session.commit()

    return jsonify({'message': 'Company registered successfully. Awaiting admin approval.'}), 201


# Login
@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate a user and return a JWT token.

    The frontend stores this token in localStorage and sends it as
    'Authorization: Bearer <token>' header on every subsequent request.
    """
    data = request.get_json() or {}

    if not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400

    # Look up the user by email.
    user = User.query.filter_by(email=data['email']).first()

    # check_password_hash compares the plain password against the stored hash.
    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401

    # Block blacklisted or deactivated accounts.
    if user.is_blacklisted:
        return jsonify({'error': 'Your account has been blacklisted. Contact admin.'}), 403
    if not user.is_active:
        return jsonify({'error': 'Your account is inactive. Contact admin.'}), 403

    # Generate a JWT token with the user's ID as the "identity" claim.
    token = create_access_token(identity=str(user.id))

    return jsonify({
        'token': token,
        'user': user.to_dict(),
        'profile': _profile_for(user),
    }), 200


# Get Current User
@auth_bp.route('/me', methods=['GET'])
@jwt_required()  # This decorator verifies the JWT token is valid
def me():
    """Return the currently logged-in user's info (used by frontend on page refresh)."""
    # get_jwt_identity() extracts the user ID we stored in the token.
    user = db.session.get(User, get_jwt_identity())
    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'user': user.to_dict(),
        'profile': _profile_for(user),
    }), 200
