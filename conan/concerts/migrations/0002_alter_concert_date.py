# Generated manually on 2026-06-27

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("concerts", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="concert",
            name="date",
            field=models.DateField(blank=True, null=True),
        ),
    ]
