from __future__ import annotations

from django.db import migrations


DEFAULT_DEPARTMENTS = [
    ("AI", "AI"),
    ("Blockchain", "BLOCKCHAIN"),
    ("DeFi", "DEFI"),
    ("CeFi", "CEFI"),
]


def seed_departments(apps, schema_editor):
    Department = apps.get_model("aka", "Department")
    for name, department_type in DEFAULT_DEPARTMENTS:
        Department.objects.get_or_create(
            name=name,
            defaults={"department_type": department_type},
        )


def unseed_departments(apps, schema_editor):
    Department = apps.get_model("aka", "Department")
    Department.objects.filter(name__in=[name for name, _ in DEFAULT_DEPARTMENTS]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("aka", "0002_alter_department_department_type"),
    ]

    operations = [
        migrations.RunPython(seed_departments, reverse_code=unseed_departments),
    ]
