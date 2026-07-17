# 🎓 Placement Portal Application

A full-stack web application for managing campus placement activities. Built for the **IITM BS Degree Programme — MAD-2 Project**.

---

## 📌 Overview

The Placement Portal connects three types of users:

- **Admin (Placement Cell)** — manages companies, students, drives, and generates reports
- **Company (Recruiter)** — registers, posts drives, manages applicants and interviews
- **Student** — registers, browses drives, applies, and tracks application status

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend API | Flask 3.1 (Python) |
| Frontend UI | Vue 3 (CDN) + Vue Router 4 |
| Styling | Bootstrap 5 + Bootstrap Icons |
| Database | SQLite (via SQLAlchemy ORM) |
| Caching | Redis (Flask-Caching) |
| Background Jobs | Celery 5 + Celery Beat |
| Authentication | JWT (Flask-JWT-Extended) |
| Email | Flask-Mail (Gmail SMTP) |
| Charts | Chart.js |

---

## 📁 Project Structure

```
placement-portal/
│
├── backend/                        ← Flask API (Python)
│   ├── app.py                      # App factory, blueprint registration
│   ├── config.py                   # All config from environment (.env)
│   ├── extensions.py               # db, cache, jwt, mail, cors singletons
│   ├── celery_app.py               # Celery factory + beat schedule
│   ├── models.py                   # Database models (ORM)
│   ├── seed_data.py                # Sample data for demo/testing
│   ├── requirements.txt            # Python dependencies
│   ├── .env.example                # Environment variable template
│   │
│   ├── routes/                     # API blueprints
│   │   ├── auth.py                 # /api/auth — login, register
│   │   ├── admin.py                # /api/admin — dashboard, approvals, search
│   │   ├── company.py              # /api/company — drives, applicants, interviews
│   │   └── student.py              # /api/student — drives, apply, export
│   │
│   ├── tasks/                      # Celery background tasks
│   │   ├── reminders.py            # Daily deadline reminder emails
│   │   ├── reports.py              # Monthly activity report to admin
│   │   └── exports.py              # Async CSV export of applications
│   │
│   ├── uploads/                    # Student resumes + exported CSVs
│   └── instance/                   # SQLite database (auto-created)
│
└── frontend/                       ← Vue 3 SPA (served by Flask)
    ├── index.html                  # SPA shell — loads CDN libs + our JS/CSS
    ├── css/
    │   └── styles.css              # Design system (tokens, layout, components)
    └── js/
        ├── app.js                  # Vue app bootstrap, axios, toast system
        ├── router.js               # Vue Router + auth guards
        ├── components/
        │   └── AppShell.js         # Reusable sidebar + topbar layout
        └── views/
            ├── Login.js            # Sign-in page
            ├── Register.js         # Registration (student / company)
            ├── AdminDashboard.js   # 6-tab admin panel with charts
            ├── CompanyDashboard.js # Drives, applicants, interviews
            └── StudentDashboard.js # Browse drives, apply, track
```

---

## ⚙️ Setup & Installation

### Prerequisites

- Python 3.10+
- Redis (running on port 6379)
  - Windows: Install [Memurai](https://www.memurai.com/get-memurai) (runs as a service automatically)
  - Linux/Mac: `sudo apt install redis-server` or `brew install redis`

### 1. Clone / Extract the project

```bash
cd placement-portal
```

### 2. Create a virtual environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / Mac
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
# Copy the example file
cp .env.example .env
```

Then open `.env` and fill in your values:

```env
# Security keys (use long random strings)
SECRET_KEY=your-long-random-secret-key
JWT_SECRET_KEY=your-long-random-jwt-key

# Redis
REDIS_URL=redis://127.0.0.1:6379/0

# Gmail SMTP (use a Google App Password, not your login password)
MAIL_USERNAME=you@gmail.com
MAIL_PASSWORD=your-16-char-app-password
MAIL_DEFAULT_SENDER=you@gmail.com

# Admin account (created automatically on first run)
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=your-admin-password

# Public URL for email links
APP_BASE_URL=http://127.0.0.1:5000
```

> **How to generate a Google App Password:**
> 1. Go to [myaccount.google.com](https://myaccount.google.com)
> 2. Security → Enable 2-Step Verification
> 3. Security → App Passwords → Generate
> 4. Copy the 16-character password into `MAIL_PASSWORD`

---

## 🚀 Running the Application

You need **3 terminal windows** open simultaneously, all inside the `backend/` folder.

### Terminal 1 — Flask App
```bash
cd backend
python app.py
```
App will be available at **http://127.0.0.1:5000**

### Terminal 2 — Celery Worker
```bash
cd backend
# Windows
celery -A app.celery worker --loglevel=info --pool=solo

# Linux / Mac
celery -A app.celery worker --loglevel=info
```

### Terminal 3 — Celery Beat (Scheduler)
```bash
cd backend
celery -A app.celery beat --loglevel=info
```

> Redis runs as a background service (Memurai on Windows) — no terminal needed.

---

## 🌱 Loading Sample Data (for Demo)

After starting the app once (to create the database), run:

```bash
cd backend
python seed_data.py
```

This creates:
- **5 companies** — TCS, Infosys, Wipro, L&T (approved) + Deloitte (pending)
- **15 students** — across CS, IT, ECE, ME, EEE, CE branches
- **6 placement drives** — mix of Full-time and Internship roles
- **20 applications** — with varied statuses (applied, shortlisted, selected, rejected)
- **7 interviews** — mix of online, in-person, and phone modes

**All passwords for sample accounts: `pass123`**

| Role | Email |
|---|---|
| Admin | set in your `.env` |
| TCS | hr@tcs.com |
| Infosys | hr@infosys.com |
| Wipro | hr@wipro.com |
| L&T | hr@larsentoubro.com |
| Deloitte (pending) | hr@deloitte.com |
| Student (selected at TCS) | aarav.mehta@jec.ac.in |
| Student (selected at Infosys) | pooja.chauhan@jec.ac.in |
| Student (selected at L&T) | prachi.agrawal@jec.ac.in |
| Student (3rd year intern) | ananya.iyer@jec.ac.in |

---

## 🔑 Features

### Admin
- Dashboard with stats, charts (Chart.js), and pending approvals
- Approve / reject company registrations and placement drives
- Blacklist or reactivate students and companies
- Search across students and companies
- View all applications with detail modals
- Monthly placement statistics

### Company
- Register and await admin approval
- Create, edit, and delete placement drives
- View and manage student applications
- Shortlist students and update application status
- Schedule / reschedule interviews (email notification sent to student)
- Set interview results (passed → selected, failed → rejected)

### Student
- Register, login, and update profile
- Upload resume (PDF, max 5MB)
- Browse approved drives with eligibility filtering and search
- Apply to eligible drives (duplicate prevention enforced)
- Track application status with interview details
- View placement history
- Export application history as CSV (async job)

### Background Jobs (Celery)
| Job | Schedule | Description |
|---|---|---|
| Daily Reminders | Every day 8:00 AM | Emails students about drives with deadlines within 3 days |
| Monthly Report | 1st of every month 9:00 AM | Sends HTML placement summary to admin |
| CSV Export | User triggered | Async export of a student's application history |

---

## 🗃️ Database Models

| Model | Description |
|---|---|
| `User` | Login credentials + role (admin/student/company) |
| `Student` | Student profile linked to User |
| `Company` | Company profile linked to User |
| `PlacementDrive` | Job posting created by a company |
| `Application` | Student applying to a drive |
| `Interview` | Interview scheduled for an application |

---

## 🌐 API Endpoints

| Prefix | Blueprint | Description |
|---|---|---|
| `/api/auth` | auth.py | Login, register student/company |
| `/api/admin` | admin.py | Dashboard, approvals, search, reports |
| `/api/company` | company.py | Drives, applicants, interviews |
| `/api/student` | student.py | Profile, drives, applications, export |

---

## 📝 Notes

- The admin account is created automatically on first run using credentials from `.env`. No admin registration is allowed.
- The database (`instance/placement.db`) is created programmatically via `db.create_all()` on startup.
- All secrets are stored in `.env` which is gitignored — never committed to version control.
- The frontend is a Vue 3 SPA served by Flask itself (same origin) — no separate build step or dev server required.
- If you don't have Redis/Celery running, set `CACHE_TYPE=SimpleCache` in `.env` — all features except email and CSV export will work.

---

## 👨‍💻 Developer

**Sanket Garg**
B.Tech — Jabalpur Engineering College (JEC)
IITM Online BS Degree Programme — Roll No: 24f3001457
MAD-2 Project — 2025
