from django.urls import path

from . import views

urlpatterns = [
    path("lead-form/", views.lead_form, name="lead_form"),
    path("leads/<int:pk>/stage/", views.lead_stage_update, name="lead_stage_update"),
    path("listings/<int:pk>/stage/", views.listing_stage_update, name="listing_stage_update"),
    path("appointments/create/", views.appointment_create, name="appointment_create"),
    path("dashboard/", views.dashboard_home, name="dashboard_home"),
    path("dashboard/staff/", views.dashboard, name="dashboard"),
    path("dashboard/customer/", views.customer_dashboard, name="customer_dashboard"),
]
