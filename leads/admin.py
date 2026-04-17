from django.contrib import admin
from .models import Appointment, Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "budget", "property_interest", "pipeline_stage", "alert_enabled", "assigned_agent", "created_at")
    search_fields = ("name", "phone", "property_interest")
    list_filter = ("pipeline_stage", "assigned_agent", "alert_enabled", "created_at")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("lead", "property", "agent", "scheduled_at")
    search_fields = ("lead__name", "property__title")
    list_filter = ("agent", "scheduled_at")
