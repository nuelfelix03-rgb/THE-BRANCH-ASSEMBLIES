# THE BRANCH ASSEMBLY

A modern, production-ready THE BRANCH ASSEMBLY web application built with Flask. Manage members, attendance, ministries, announcements, events, and generate reports.

## Features

- **Authentication** - Role-based access (Super Admin, Church Admin, Ministry Leader, Member)
- **Dashboard** - Statistics, member growth chart, upcoming events, recent announcements
- **Member Management** - Full CRUD with search, filter, CSV export, profile pictures
- **Attendance Tracking** - Individual and bulk marking, statistics, monthly/ weekly reports
- **Ministries & Departments** - Manage church groups, assign members, view stats
- **Announcements** - Create, schedule, publish with category filtering
- **Events** - Create, manage, calendar view with FullCalendar integration
- **Reports** - Member and attendance reports with CSV export and Chart.js visualizations
- **Notifications** - In-app notification system with read/unread tracking

## Tech Stack

- **Backend:** Python, Flask, SQLAlchemy, Flask-Login, Flask-WTF, Flask-Migrate
- **Frontend:** HTML5, CSS3, Bootstrap 5, JavaScript, Chart.js, FullCalendar
- **Database:** SQLite (dev), PostgreSQL-ready (production)
- **Tools:** Jinja2, python-dotenv, Pillow

## Quick Start

```bash
# 1. Clone the repository
git clone <repo-url>
cd church_management_system

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
# Edit .env with your settings (or use defaults)

# 4. Run the application
python run.py
```

The app creates an SQLite database automatically on first run with a default admin account.

## Default Login

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Super Admin |

**Change these credentials immediately in production.**

## Project Structure

```
church_management_system/
├── app/
│   ├── __init__.py          # Application factory
│   ├── models.py            # SQLAlchemy models
│   ├── forms.py             # WTForms
│   ├── routes/              # Blueprints (auth, members, attendance, etc.)
│   ├── services/            # Business logic
│   ├── templates/           # Jinja2 templates
│   ├── static/              # CSS, JS, uploads
│   └── utils/               # Decorators, helpers, seed data
├── config.py                # Configuration
├── requirements.txt         # Python dependencies
├── run.py                   # Entry point
├── .env                     # Environment variables
└── README.md
```

## User Roles

- **Super Admin** - Full access to all features including system settings
- **Church Admin** - Manage members, attendance, announcements, events
- **Ministry Leader** - View ministry members, record ministry attendance
- **Member** - View profile, announcements, upcoming events

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| SECRET_KEY | Flask secret key | dev-secret-key-change-in-production |
| DATABASE_URL | Database connection | sqlite:///church.db |
| MAIL_SERVER | SMTP server | smtp.gmail.com |
| MAIL_PORT | SMTP port | 587 |
| MAIL_USE_TLS | Use TLS | True |

## API Endpoints

- `/events/api/events` - JSON endpoint for calendar events
- `/notifications/unread-count` - JSON endpoint for unread notification count
- `/members/export` - CSV export of all members
- `/reports/export/members/csv` - Members report CSV
- `/reports/export/attendance/csv` - Attendance report CSV

## Future Enhancements

- Finance and donations management
- Online member portal
- Email/SMS notification delivery
- Advanced reporting (PDF export)
- Prayer request module
- Sermon management
- Mobile app integration
