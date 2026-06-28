# Generated manually on 2026-06-28

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("concerts", "0003_concert_archived"),
    ]

    operations = [
        migrations.AddField(
            model_name="concert",
            name="concert_negi",
            field=models.BooleanField(default=False),
        ),
    ]
