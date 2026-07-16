from django.core.management.base import BaseCommand

from tracker.models import Category

DEFAULTS = [
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
    help = "Seed the default task categories"

    def handle(self, *args, **options):
        created = 0
        for name, description in DEFAULTS:
            _, was_created = Category.objects.get_or_create(
                name=name, defaults={"description": description})
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(
            f"Categories ready ({created} newly created)."))
