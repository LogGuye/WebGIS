from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("properties", "0002_property_phase2_fields_and_changelog"),
    ]

    operations = [
        migrations.CreateModel(
            name="PropertyImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to="properties/")),
                ("caption", models.CharField(blank=True, max_length=255)),
                ("is_primary", models.BooleanField(default=False)),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("property", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="images", to="properties.property")),
            ],
            options={"ordering": ["sort_order", "id"]},
        ),
    ]
