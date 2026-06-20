from django.db import migrations


def remove_legacy_departments(apps, schema_editor):
    Department = apps.get_model("aka", "Department")
    Department.objects.filter(name__in=["Sales", "AI Showcases"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("aka", "0004_alter_department_department_type"),
    ]

    operations = [
        migrations.RunPython(remove_legacy_departments, reverse_code=migrations.RunPython.noop),
    ]
