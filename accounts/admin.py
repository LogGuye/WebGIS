from django.contrib import admin

from .models import Agent


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email")
    search_fields = ("name", "phone", "email")
    list_filter = ()
