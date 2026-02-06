from django.db import migrations, models
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Amenity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=255)),
                ("amenity_type", models.CharField(choices=[("school", "School"), ("hospital", "Hospital"), ("park", "Park"), ("mall", "Mall"), ("supermarket", "Supermarket"), ("transport", "Transport Hub"), ("other", "Other")], default="other", max_length=32)),
                ("location", django.contrib.gis.db.models.fields.PointField(geography=True, srid=4326)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Property",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("property_type", models.CharField(choices=[("apartment", "Apartment"), ("house", "House"), ("land", "Land")], max_length=20)),
                ("price", models.DecimalField(decimal_places=2, max_digits=14)),
                ("area", models.FloatField(help_text="Area in square meters")),
                ("address", models.CharField(max_length=255)),
                ("location", django.contrib.gis.db.models.fields.PointField(geography=True, srid=4326)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("agent", models.ForeignKey(blank=True, null=True, on_delete=models.deletion.SET_NULL, related_name="properties", to="accounts.agent")),
                ("amenities", models.ManyToManyField(blank=True, related_name="properties", to="properties.Amenity")),
            ],
            options={"ordering": ["title"]},
        ),
    ]
