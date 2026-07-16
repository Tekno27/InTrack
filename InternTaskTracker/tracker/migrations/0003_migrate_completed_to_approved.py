from django.db import migrations


def forwards(apps, schema_editor):
    Task = apps.get_model("tracker", "Task")
    Task.objects.filter(status="COMPLETED").update(status="APPROVED")


def backwards(apps, schema_editor):
    Task = apps.get_model("tracker", "Task")
    Task.objects.filter(status="APPROVED").update(status="COMPLETED")


class Migration(migrations.Migration):

    dependencies = [
        ("tracker", "0002_alter_task_status_taskreview"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
