from django.urls import path

from . import admin_api, views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("admin-api/leads/", admin_api.admin_leads_collection, name="admin_leads_collection"),
    path("admin-api/leads/<int:pk>/", admin_api.admin_lead_record, name="admin_lead_record"),
    path("admin-api/agents/", admin_api.admin_agents_collection, name="admin_agents_collection"),
    path("admin-api/agents/<int:pk>/", admin_api.admin_agent_record, name="admin_agent_record"),
    path("admin-api/amenities/", admin_api.admin_amenities_collection, name="admin_amenities_collection"),
    path("admin-api/amenities/<int:pk>/", admin_api.admin_amenity_record, name="admin_amenity_record"),
    path('about/', views.about_view, name='about'),
]
