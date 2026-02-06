from django.db import migrations, models
import django.contrib.gis.db.models.fields
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
        ("properties", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Lead",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("phone", models.CharField(max_length=20)),
                ("budget", models.DecimalField(decimal_places=2, max_digits=14)),
                ("desired_location", django.contrib.gis.db.models.fields.PointField(geography=True, srid=4326)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("assigned_agent", models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name="leads", to="accounts.agent")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Appointment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("scheduled_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("notes", models.TextField(blank=True)),
                ("agent", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="appointments", to="accounts.agent")),
                ("lead", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="appointments", to="leads.lead")),
                ("property", models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="appointments", to="properties.property")),
            ],
            options={"ordering": ["-scheduled_at"]},
        ),
    ]
