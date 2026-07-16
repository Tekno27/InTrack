# InTrack — Intern Task & Time Tracker

A modern web-based internship management system that lets interns record daily work and track time spent on tasks, while supervisors monitor progress through dashboards, reports, and analytics.

Developed as a final internship project by **Nii Teiko Aryee** (University of Cape Coast).

---

## Features

- Role-based authentication (Intern / Supervisor)
- Intern self-registration and password reset
- Daily task logging with start/end time and auto-calculated duration
- Task categories, priorities, statuses, attachments, and notes
- Intern dashboard (hours today / week / month, charts, recent activity)
- Supervisor dashboard (interns, tasks, top performers, weekly analytics)
- Search & filtering by date, status, priority, category, and intern
- Reports with PDF, Excel, and CSV export
- Analytics charts (Chart.js)
- User profile with department, phone, and profile picture
- Optional in-app notifications

---

## Tech Stack

| Layer      | Technology                          |
|------------|-------------------------------------|
| Backend    | Django 6, Python 3.13+              |
| Database   | SQLite (dev) / PostgreSQL (prod)    |
| Frontend   | HTML5, CSS3, Bootstrap 5, Chart.js  |
| Reports    | ReportLab, OpenPyXL                 |
| Forms      | django-crispy-forms + Bootstrap 5   |

---

## Project Structure

```
InternTaskTracker/
├── accounts/          (handled inside tracker app)
├── config/            # Django project settings
├── tracker/           # Core app (models, views, urls, forms)
├── templates/         # HTML templates
├── static/            # CSS / JS
├── media/             # Uploaded files
├── manage.py
├── requirements.txt
└── README.md
```

---

## Installation

```bash
# 1. Clone the repository
git clone <repository-url>
cd InternTaskTracker

# 2. Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
python manage.py migrate

# 5. Seed default task categories
python manage.py seed_categories

# 6. Create a supervisor (admin) account
python manage.py createsuperuser
# Then set role=SUPERVISOR in the Django admin, or via shell:
#   python manage.py shell
#   >>> from tracker.models import User
#   >>> u = User.objects.get(username='yourname')
#   >>> u.role = User.Roles.SUPERVISOR
#   >>> u.save()

# 7. Start the development server
python manage.py runserver
```

Open http://127.0.0.1:8000/

Interns can self-register at `/register/`. Supervisors are created via the admin or shell.

---

## Default Categories

Development · Research · Documentation · Meeting · Training · Testing · Deployment · Other

---

## User Roles

### Intern
Register/login · Dashboard · Create / edit / delete own tasks · Upload attachments · View stats · Export personal reports · Manage profile

### Supervisor
Login · View all interns · View every submitted task · Search / filter · Analytics · Export reports

---

## UI Theme

| Token     | Color   |
|-----------|---------|
| Primary   | `#2563EB` |
| Success   | `#16A34A` |
| Warning   | `#F59E0B` |
| Danger    | `#DC2626` |
| Background| `#F8FAFC` |

Font: Inter

---

## License

This project is developed for academic and portfolio purposes.
