"""
seed_data.py — Populate the database with realistic Indian sample data.

Run AFTER the app has started at least once (so tables exist):
    python seed_data.py

This creates:
  - 5 companies (mix of IT, consulting, manufacturing)
  - 15 students across branches
  - 6 placement drives
  - ~20 applications with varied statuses
  - A few scheduled interviews

Safe to run multiple times — it checks if data already exists.
"""

import os
import sys
from datetime import date, datetime, timedelta, timezone

from dotenv import load_dotenv

# Load .env before importing anything that reads config
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'), override=True)

from werkzeug.security import generate_password_hash

from app import flask_app
from extensions import db
from models import User, Student, Company, PlacementDrive, Application, Interview


def seed():
    """Insert sample data if the database is empty (only admin exists)."""

    with flask_app.app_context():
        # Skip if students already exist (avoid duplicate seeding)
        if Student.query.first():
            print("Database already has data. Delete instance/placement.db and restart to re-seed.")
            return

        print("Seeding sample data...")

        # ── Helper to create a user + return the user object ────────
        def make_user(email, password, role):
            u = User(
                email=email,
                password_hash=generate_password_hash(password),
                role=role,
                is_active=True,
                is_blacklisted=False,
            )
            db.session.add(u)
            db.session.flush()
            return u

        # ════════════════════════════════════════════════════════════
        #  COMPANIES (5 companies — all use password "pass123")
        # ════════════════════════════════════════════════════════════
        companies_data = [
            {
                'email': 'hr@tcs.com', 'company_name': 'Tata Consultancy Services',
                'hr_name': 'Priya Sharma', 'hr_email': 'priya.sharma@tcs.com',
                'website': 'https://www.tcs.com', 'industry': 'IT Services',
                'description': 'Leading global IT services, consulting and business solutions company.',
                'status': 'approved',
            },
            {
                'email': 'hr@infosys.com', 'company_name': 'Infosys Limited',
                'hr_name': 'Rahul Verma', 'hr_email': 'rahul.verma@infosys.com',
                'website': 'https://www.infosys.com', 'industry': 'IT Services',
                'description': 'Digital services and consulting company headquartered in Bengaluru.',
                'status': 'approved',
            },
            {
                'email': 'hr@wipro.com', 'company_name': 'Wipro Technologies',
                'hr_name': 'Anjali Gupta', 'hr_email': 'anjali.gupta@wipro.com',
                'website': 'https://www.wipro.com', 'industry': 'IT Services',
                'description': 'Global information technology, consulting and business process services company.',
                'status': 'approved',
            },
            {
                'email': 'hr@larsentoubro.com', 'company_name': 'Larsen & Toubro',
                'hr_name': 'Vikram Singh', 'hr_email': 'vikram.singh@lnt.com',
                'website': 'https://www.larsentoubro.com', 'industry': 'Engineering & Construction',
                'description': 'Indian multinational in EPC projects, hi-tech manufacturing and services.',
                'status': 'approved',
            },
            {
                'email': 'hr@deloitte.com', 'company_name': 'Deloitte India',
                'hr_name': 'Neha Patel', 'hr_email': 'neha.patel@deloitte.com',
                'website': 'https://www.deloitte.com/in', 'industry': 'Consulting',
                'description': 'Professional services network providing audit, consulting, tax and advisory.',
                'status': 'pending',
            },
        ]

        company_objs = []
        for c in companies_data:
            user = make_user(c['email'], 'pass123', 'company')
            company = Company(
                user_id=user.id,
                company_name=c['company_name'],
                hr_name=c['hr_name'],
                hr_email=c['hr_email'],
                website=c['website'],
                industry=c['industry'],
                description=c['description'],
                approval_status=c['status'],
            )
            db.session.add(company)
            db.session.flush()
            company_objs.append(company)
            print(f"  Company: {c['company_name']} ({c['status']})")

        # ════════════════════════════════════════════════════════════
        #  STUDENTS (15 students — all use password "pass123")
        # ════════════════════════════════════════════════════════════
        students_data = [
            {'email': 'aarav.mehta@jec.ac.in', 'full_name': 'Aarav Mehta', 'roll_number': '21CS001', 'branch': 'CS', 'cgpa': 8.7, 'year': 4, 'phone': '9876543210'},
            {'email': 'isha.reddy@jec.ac.in', 'full_name': 'Isha Reddy', 'roll_number': '21CS002', 'branch': 'CS', 'cgpa': 9.1, 'year': 4, 'phone': '9876543211'},
            {'email': 'rohan.joshi@jec.ac.in', 'full_name': 'Rohan Joshi', 'roll_number': '21CS003', 'branch': 'CS', 'cgpa': 7.4, 'year': 4, 'phone': '9876543212'},
            {'email': 'ananya.iyer@jec.ac.in', 'full_name': 'Ananya Iyer', 'roll_number': '22CS001', 'branch': 'CS', 'cgpa': 8.2, 'year': 3, 'phone': '9876543213'},
            {'email': 'dev.kumar@jec.ac.in', 'full_name': 'Dev Kumar', 'roll_number': '21IT001', 'branch': 'IT', 'cgpa': 8.0, 'year': 4, 'phone': '9876543214'},
            {'email': 'kavya.nair@jec.ac.in', 'full_name': 'Kavya Nair', 'roll_number': '21IT002', 'branch': 'IT', 'cgpa': 7.8, 'year': 4, 'phone': '9876543215'},
            {'email': 'arjun.das@jec.ac.in', 'full_name': 'Arjun Das', 'roll_number': '21IT003', 'branch': 'IT', 'cgpa': 6.9, 'year': 4, 'phone': '9876543216'},
            {'email': 'sneha.mishra@jec.ac.in', 'full_name': 'Sneha Mishra', 'roll_number': '21ECE001', 'branch': 'ECE', 'cgpa': 8.5, 'year': 4, 'phone': '9876543217'},
            {'email': 'aditya.pandey@jec.ac.in', 'full_name': 'Aditya Pandey', 'roll_number': '21ECE002', 'branch': 'ECE', 'cgpa': 7.6, 'year': 4, 'phone': '9876543218'},
            {'email': 'pooja.chauhan@jec.ac.in', 'full_name': 'Pooja Chauhan', 'roll_number': '21ECE003', 'branch': 'ECE', 'cgpa': 9.0, 'year': 4, 'phone': '9876543219'},
            {'email': 'vikash.yadav@jec.ac.in', 'full_name': 'Vikash Yadav', 'roll_number': '21ME001', 'branch': 'ME', 'cgpa': 7.3, 'year': 4, 'phone': '9876543220'},
            {'email': 'riya.saxena@jec.ac.in', 'full_name': 'Riya Saxena', 'roll_number': '21ME002', 'branch': 'ME', 'cgpa': 8.1, 'year': 4, 'phone': '9876543221'},
            {'email': 'harsh.tiwari@jec.ac.in', 'full_name': 'Harsh Tiwari', 'roll_number': '21EEE001', 'branch': 'EEE', 'cgpa': 7.9, 'year': 4, 'phone': '9876543222'},
            {'email': 'prachi.agrawal@jec.ac.in', 'full_name': 'Prachi Agrawal', 'roll_number': '21CE001', 'branch': 'CE', 'cgpa': 8.4, 'year': 4, 'phone': '9876543223'},
            {'email': 'manish.dubey@jec.ac.in', 'full_name': 'Manish Dubey', 'roll_number': '21CE002', 'branch': 'CE', 'cgpa': 6.5, 'year': 4, 'phone': '9876543224'},
        ]

        student_objs = []
        for s in students_data:
            user = make_user(s['email'], 'pass123', 'student')
            student = Student(
                user_id=user.id,
                full_name=s['full_name'],
                roll_number=s['roll_number'],
                branch=s['branch'],
                cgpa=s['cgpa'],
                year_of_study=s['year'],
                phone=s['phone'],
            )
            db.session.add(student)
            db.session.flush()
            student_objs.append(student)
            print(f"  Student: {s['full_name']} ({s['branch']}, CGPA {s['cgpa']})")

        # ════════════════════════════════════════════════════════════
        #  PLACEMENT DRIVES (6 drives from approved companies)
        # ════════════════════════════════════════════════════════════
        tcs, infosys, wipro, lnt = company_objs[0], company_objs[1], company_objs[2], company_objs[3]

        drives_data = [
            {
                'company': tcs, 'title': 'Software Developer',
                'desc': 'Develop and maintain enterprise applications using Java, Spring Boot and microservices. Training provided for freshers.',
                'branches': 'CS,IT', 'cgpa': 7.0, 'year': 4,
                'deadline': date.today() + timedelta(days=15),
                'status': 'approved', 'type': 'Full-time', 'package': 7.0,
            },
            {
                'company': infosys, 'title': 'Systems Engineer',
                'desc': 'Join as a Systems Engineer in Infosys Digital. Work on cloud migration, DevOps and full-stack development projects.',
                'branches': 'CS,IT,ECE', 'cgpa': 6.5, 'year': 4,
                'deadline': date.today() + timedelta(days=20),
                'status': 'approved', 'type': 'Full-time', 'package': 6.5,
            },
            {
                'company': wipro, 'title': 'Project Engineer',
                'desc': 'Work on client-facing projects in domains like BFSI, healthcare and retail. Technologies include Python, React and AWS.',
                'branches': 'CS,IT,ECE,EEE', 'cgpa': 6.0, 'year': 4,
                'deadline': date.today() + timedelta(days=10),
                'status': 'approved', 'type': 'Full-time', 'package': 5.5,
            },
            {
                'company': tcs, 'title': 'Digital Intern',
                'desc': 'Summer internship in TCS Digital division. Work on AI/ML projects with mentorship from senior architects.',
                'branches': 'CS,IT', 'cgpa': 8.0, 'year': 3,
                'deadline': date.today() + timedelta(days=25),
                'status': 'approved', 'type': 'Internship', 'package': 1.2,
            },
            {
                'company': lnt, 'title': 'Graduate Engineer Trainee',
                'desc': 'Join L&T Construction as GET. Rotation across project sites, design offices and client coordination.',
                'branches': 'ME,CE,EEE', 'cgpa': 7.0, 'year': 4,
                'deadline': date.today() + timedelta(days=30),
                'status': 'approved', 'type': 'Full-time', 'package': 8.0,
            },
            {
                'company': infosys, 'title': 'Data Analyst',
                'desc': 'Analyze business data using SQL, Python and Power BI. Strong analytical and communication skills required.',
                'branches': 'CS,IT', 'cgpa': 7.5, 'year': 4,
                'deadline': date.today() + timedelta(days=5),
                'status': 'pending',
                'type': 'Full-time', 'package': 8.5,
            },
        ]

        drive_objs = []
        for d in drives_data:
            drive = PlacementDrive(
                company_id=d['company'].id,
                job_title=d['title'],
                job_description=d['desc'],
                eligible_branches=d['branches'],
                min_cgpa=d['cgpa'],
                eligible_year=d['year'],
                application_deadline=d['deadline'],
                status=d['status'],
                job_type=d['type'],
                package_lpa=d['package'],
            )
            db.session.add(drive)
            db.session.flush()
            drive_objs.append(drive)
            print(f"  Drive: {d['title']} @ {d['company'].company_name} ({d['status']})")

        # ════════════════════════════════════════════════════════════
        #  APPLICATIONS (students applying to approved drives)
        # ════════════════════════════════════════════════════════════
        applications_data = [
            # TCS Software Developer (CS,IT, min 7.0)
            {'student': 0, 'drive': 0, 'status': 'selected',     'days_ago': 10},
            {'student': 1, 'drive': 0, 'status': 'shortlisted',  'days_ago': 10},
            {'student': 2, 'drive': 0, 'status': 'applied',      'days_ago': 8},
            {'student': 4, 'drive': 0, 'status': 'shortlisted',  'days_ago': 9},
            {'student': 5, 'drive': 0, 'status': 'rejected',     'days_ago': 10},

            # Infosys Systems Engineer (CS,IT,ECE, min 6.5)
            {'student': 0, 'drive': 1, 'status': 'applied',      'days_ago': 5},
            {'student': 1, 'drive': 1, 'status': 'shortlisted',  'days_ago': 5},
            {'student': 4, 'drive': 1, 'status': 'applied',      'days_ago': 4},
            {'student': 7, 'drive': 1, 'status': 'shortlisted',  'days_ago': 5},
            {'student': 8, 'drive': 1, 'status': 'applied',      'days_ago': 3},
            {'student': 9, 'drive': 1, 'status': 'selected',     'days_ago': 5},

            # Wipro Project Engineer (CS,IT,ECE,EEE, min 6.0)
            {'student': 2, 'drive': 2, 'status': 'applied',      'days_ago': 6},
            {'student': 5, 'drive': 2, 'status': 'applied',      'days_ago': 6},
            {'student': 6, 'drive': 2, 'status': 'applied',      'days_ago': 4},
            {'student': 12, 'drive': 2, 'status': 'shortlisted', 'days_ago': 5},

            # TCS Digital Intern (CS,IT, min 8.0, year 3)
            {'student': 3, 'drive': 3, 'status': 'applied',      'days_ago': 2},

            # L&T GET (ME,CE,EEE, min 7.0)
            {'student': 10, 'drive': 4, 'status': 'applied',     'days_ago': 7},
            {'student': 11, 'drive': 4, 'status': 'shortlisted', 'days_ago': 7},
            {'student': 12, 'drive': 4, 'status': 'applied',     'days_ago': 6},
            {'student': 13, 'drive': 4, 'status': 'selected',    'days_ago': 7},
        ]

        app_objs = []
        for a in applications_data:
            student = student_objs[a['student']]
            drive = drive_objs[a['drive']]
            application = Application(
                student_id=student.id,
                drive_id=drive.id,
                application_date=date.today() - timedelta(days=a['days_ago']),
                status=a['status'],
                resume_snapshot=student.resume_path,
            )
            db.session.add(application)
            db.session.flush()
            app_objs.append(application)

        print(f"  Applications: {len(applications_data)} created")

        # ════════════════════════════════════════════════════════════
        #  INTERVIEWS (for shortlisted/selected students)
        # ════════════════════════════════════════════════════════════
        interviews_data = [
            {
                'app_index': 0,
                'scheduled': datetime.now(timezone.utc) - timedelta(days=3),
                'mode': 'Online', 'location': 'Google Meet — meet.google.com/tcs-aarav',
                'notes': 'DSA + System Design round. 45 minutes.',
                'result': 'passed',
            },
            {
                'app_index': 1,
                'scheduled': datetime.now(timezone.utc) + timedelta(days=2),
                'mode': 'Online', 'location': 'Microsoft Teams link shared via email',
                'notes': 'Technical + HR round. Carry your resume.',
                'result': 'pending',
            },
            {
                'app_index': 3,
                'scheduled': datetime.now(timezone.utc) + timedelta(days=3),
                'mode': 'In-Person', 'location': 'JEC Seminar Hall, Block A',
                'notes': 'On-campus drive. Bring college ID.',
                'result': 'pending',
            },
            {
                'app_index': 8,
                'scheduled': datetime.now(timezone.utc) + timedelta(days=5),
                'mode': 'Online', 'location': 'Zoom — link will be emailed 1 hour before',
                'notes': 'Aptitude + Technical interview.',
                'result': 'pending',
            },
            {
                'app_index': 10,
                'scheduled': datetime.now(timezone.utc) - timedelta(days=2),
                'mode': 'Online', 'location': 'Google Meet',
                'notes': 'Final HR round.',
                'result': 'passed',
            },
            {
                'app_index': 19,
                'scheduled': datetime.now(timezone.utc) - timedelta(days=1),
                'mode': 'In-Person', 'location': 'L&T Office, Powai, Mumbai',
                'notes': 'Technical + project discussion. Travel reimbursed.',
                'result': 'passed',
            },
            {
                'app_index': 17,
                'scheduled': datetime.now(timezone.utc) + timedelta(days=4),
                'mode': 'Phone', 'location': 'HR will call on registered number',
                'notes': 'Telephonic screening round.',
                'result': 'pending',
            },
        ]

        for iv in interviews_data:
            interview = Interview(
                application_id=app_objs[iv['app_index']].id,
                scheduled_at=iv['scheduled'],
                mode=iv['mode'],
                location=iv['location'],
                notes=iv['notes'],
                result=iv['result'],
            )
            db.session.add(interview)

        print(f"  Interviews: {len(interviews_data)} scheduled")

        # ════════════════════════════════════════════════════════════
        #  COMMIT EVERYTHING
        # ════════════════════════════════════════════════════════════
        db.session.commit()

        print("\n✅ Sample data seeded successfully!")
        print("\n── Login credentials (all passwords: pass123) ──")
        print(f"  Admin:   (use credentials from your .env file)")
        print(f"  Students: aarav.mehta@jec.ac.in, isha.reddy@jec.ac.in, rohan.joshi@jec.ac.in, etc.")
        print(f"  Companies: hr@tcs.com, hr@infosys.com, hr@wipro.com, hr@larsentoubro.com")
        print(f"  Pending company: hr@deloitte.com (needs admin approval)")
        print(f"  Pending drive: Infosys 'Data Analyst' (needs admin approval)")


if __name__ == '__main__':
    seed()