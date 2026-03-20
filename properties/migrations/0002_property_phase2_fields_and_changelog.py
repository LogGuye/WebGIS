from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("properties", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="property",
            name="is_featured",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="property",
            name="listing_status",
            field=models.CharField(
                choices=[("active", "Active"), ("sold", "Sold"), ("hidden", "Hidden")],
                default="active",
                max_length=20,
            ),
        ),
        migrations.CreateModel(
            name="PropertyChangeLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(max_length=32)),
                ("summary", models.CharField(blank=True, max_length=255)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "property",
                    models.ForeignKey(on_delete=models.deletion.CASCADE, related_name="change_logs", to="properties.property"),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
    ]
