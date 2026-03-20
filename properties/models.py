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

    class ListingStatus(models.TextChoices):
        ACTIVE = "active", _("Active")
        SOLD = "sold", _("Sold")
        HIDDEN = "hidden", _("Hidden")

    agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True, related_name="properties")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    property_type = models.CharField(max_length=20, choices=PropertyType.choices)
    listing_status = models.CharField(max_length=20, choices=ListingStatus.choices, default=ListingStatus.ACTIVE)
    is_featured = models.BooleanField(default=False)
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

    @property
    def primary_image(self):
        primary = self.images.filter(is_primary=True).order_by("sort_order", "id").first()
        return primary or self.images.order_by("sort_order", "id").first()

    @property
    def primary_image_url(self):
        image = self.primary_image
        return image.image.url if image and image.image else None


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="properties/")
    caption = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["sort_order", "id"]

    def __str__(self):
        return f"Image for {self.property.title}"


class PropertyChangeLog(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="change_logs")
    action = models.CharField(max_length=32)
    summary = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.property.title} - {self.action}"
