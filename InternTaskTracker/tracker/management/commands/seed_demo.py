from django.core.management.base import BaseCommand

from tracker.models import Category, Department, User


DEFAULT_CATEGORIES = [
    ("Development", "Software development and coding work"),
    ("Research", "Research and investigation activities"),
    ("Documentation", "Writing documentation and reports"),
    ("Meeting", "Meetings and discussions"),
    ("Training", "Training sessions and learning"),
    ("Testing", "QA and testing activities"),
    ("Deployment", "Deployment and release work"),
    ("Other", "Other internship activities"),
]


class Command(BaseCommand):
    help = "Seed departments, categories, and demo users for local development"

    def handle(self, *args, **options):
        it, _ = Department.objects.get_or_create(
            name="IT Department",
            defaults={"description": "Information Technology"},
        )
        hr, _ = Department.objects.get_or_create(
            name="HR Department",
            defaults={"description": "Human Resources"},
        )

        for name, description in DEFAULT_CATEGORIES:
            Category.objects.get_or_create(
                name=name, department=None, defaults={"description": description})

        head, created = User.objects.get_or_create(
            username="head",
            defaults={
                "email": "head@intrack.local",
                "first_name": "Kwame",
                "last_name": "Owusu",
                "role": User.Roles.HEAD,
                "department": it,
                "email_verified": True,
                "must_set_password": False,
            },
        )
        if created:
            head.set_password("head123")
            head.save()
        else:
            head.role = User.Roles.HEAD
            head.department = it
            head.email_verified = True
            head.must_set_password = False
            head.set_password("head123")
            head.save()

        supervisor, created = User.objects.get_or_create(
            username="supervisor",
            defaults={
                "email": "supervisor@intrack.local",
                "first_name": "Ama",
                "last_name": "Mensah",
                "role": User.Roles.SUPERVISOR,
                "department": it,
                "email_verified": True,
                "must_set_password": False,
            },
        )
        if created:
            supervisor.set_password("supervisor123")
            supervisor.save()
        else:
            supervisor.role = User.Roles.SUPERVISOR
            supervisor.department = it
            supervisor.email_verified = True
            supervisor.must_set_password = False
            supervisor.set_password("supervisor123")
            supervisor.save()

        intern, created = User.objects.get_or_create(
            username="intern",
            defaults={
                "email": "intern@intrack.local",
                "first_name": "Nii",
                "last_name": "Aryee",
                "role": User.Roles.INTERN,
                "department": it,
                "supervisor": supervisor,
                "email_verified": True,
                "must_set_password": False,
            },
        )
        if created:
            intern.set_password("intern123")
            intern.save()
        else:
            intern.role = User.Roles.INTERN
            intern.department = it
            intern.supervisor = supervisor
            intern.email_verified = True
            intern.must_set_password = False
            intern.set_password("intern123")
            intern.save()

        # Optional second department head for isolation demos
        hr_head, created = User.objects.get_or_create(
            username="hrhead",
            defaults={
                "email": "hrhead@intrack.local",
                "first_name": "Efua",
                "last_name": "Boateng",
                "role": User.Roles.HEAD,
                "department": hr,
                "email_verified": True,
                "must_set_password": False,
            },
        )
        if created:
            hr_head.set_password("hrhead123")
            hr_head.save()

        self.stdout.write(self.style.SUCCESS("Demo data ready:"))
        self.stdout.write("  head / head123         (IT Department Head)")
        self.stdout.write("  supervisor / supervisor123")
        self.stdout.write("  intern / intern123")
        self.stdout.write("  hrhead / hrhead123     (HR Department Head)")
