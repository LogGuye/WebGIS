from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin
from .models import Appointment, Lead


@admin.register(Lead)
class LeadAdmin(GISModelAdmin):
    list_display = ("name", "phone", "budget", "assigned_agent", "created_at")
    search_fields = ("name", "phone")
    list_filter = ("assigned_agent",)


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("lead", "property", "agent", "scheduled_at")
    search_fields = ("lead__name", "property__title")
    list_filter = ("agent", "scheduled_at")
