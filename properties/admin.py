from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from .models import Amenity, Property


@admin.register(Property)
class PropertyAdmin(GISModelAdmin):
    list_display = ("title", "property_type", "price", "area", "agent")
    search_fields = ("title", "address", "description")
    list_filter = ("property_type", "agent")
    filter_horizontal = ("amenities",)


@admin.register(Amenity)
class AmenityAdmin(GISModelAdmin):
    list_display = ("name", "amenity_type")
    list_filter = ("amenity_type",)
    search_fields = ("name",)
