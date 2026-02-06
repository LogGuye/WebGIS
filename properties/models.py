from django.contrib.gis.db import models
from django.utils.translation import gettext_lazy as _

from accounts.models import Agent


class Amenity(models.Model):
    class AmenityType(models.TextChoices):
        SCHOOL = "school", _("School")
        HOSPITAL = "hospital", _("Hospital")
        PARK = "park", _("Park")
        MALL = "mall", _("Mall")
        SUPERMARKET = "supermarket", _("Supermarket")
        TRANSPORT = "transport", _("Transport Hub")
        OTHER = "other", _("Other")

    name = models.CharField(max_length=255)
    amenity_type = models.CharField(max_length=32, choices=AmenityType.choices, default=AmenityType.OTHER)
    location = models.PointField(geography=True, srid=4326)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.get_amenity_type_display()} - {self.name}"


class Property(models.Model):
    class PropertyType(models.TextChoices):
        APARTMENT = "apartment", _("Apartment")
        HOUSE = "house", _("House")
        LAND = "land", _("Land")

    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True, related_name="properties")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    property_type = models.CharField(max_length=20, choices=PropertyType.choices)
    price = models.DecimalField(max_digits=14, decimal_places=2)
    area = models.FloatField(help_text="Area in square meters")
    address = models.CharField(max_length=255)
    location = models.PointField(geography=True, srid=4326)
    amenities = models.ManyToManyField(Amenity, blank=True, related_name="properties")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title
