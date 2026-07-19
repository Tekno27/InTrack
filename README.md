# InTrack — Intern Task & Time Tracker

A department-based internship management system where department heads onboard supervisors and interns, interns log time on tasks (and receive assigned work), supervisors monitor their teams, and everyone can chat within clear permission rules.

Developed as a final internship project by **Nii Teiko Aryee** (University of Cape Coast).

---

## Roles (RBAC)

| Role | Who creates them | What they can do |
|------|------------------|------------------|
| **System Admin** | Django admin | Create departments and department heads |
| **Department Head** | System admin | Invite supervisors/interns, assign interns to supervisors, oversee department tasks/analytics, chat |
| **Supervisor** | Department head (invite) | Assign tasks to their interns, monitor team, chat |
| **Intern** | Department head (invite) | Log personal work, update assigned tasks, chat |

Public self-registration is disabled. Invited users get an email link to verify their email and set a password.

---

## Chat rules

- Intern ↔ other interns in the **same department**
- Intern ↔ their **assigned supervisor** and **department head**
- Supervisors / heads ↔ any other supervisor / head (**company-wide**)

---

## Task model

- Interns can **log their own work** (date + start/end time → auto duration)
- Supervisors / heads can **assign tasks** to interns they manage
- Interns update status / log time on assigned tasks

---

## Quick start

```bash
cd InternTaskTracker
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open http://127.0.0.1:8000/

### Demo accounts

| Username | Password | Role |
|----------|----------|------|
| `head` | `head123` | IT Department Head |
| `supervisor` | `supervisor123` | IT Supervisor |
| `intern` | `intern123` | IT Intern (assigned to supervisor) |
| `hrhead` | `hrhead123` | HR Department Head |

Invite emails print to the terminal in development (`EMAIL_BACKEND = console`).

### Creating a real department head

1. `python manage.py createsuperuser`
2. In `/admin/`, create a **Department**
3. Create a **User** with role `HEAD`, link them to that department, set a password (or leave invite flow for later)

---

## Stack

Django 6 · Bootstrap 5 · Chart.js · ReportLab · OpenPyXL · SQLite (dev)

---

## License

Academic / portfolio use.
