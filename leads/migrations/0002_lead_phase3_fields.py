from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("leads", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="lead",
            name="alert_enabled",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="lead",
            name="notes",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="lead",
            name="property_interest",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
