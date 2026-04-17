from django.contrib import admin

from .models import Agent, UserProfile


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ("name", "phone", "email")
    search_fields = ("name", "phone", "email")
    list_filter = ()


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "linked_agent", "updated_at")
    search_fields = ("user__username", "user__email")
    list_filter = ("role",)
