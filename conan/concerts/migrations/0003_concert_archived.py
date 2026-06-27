# Generated manually on 2026-06-27

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("concerts", "0002_alter_concert_date"),
    ]

    operations = [
        migrations.AddField(
            model_name="concert",
            name="archived",
            field=models.BooleanField(default=False),
        ),
    ]
