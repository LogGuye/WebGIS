from django.urls import path

from . import views

urlpatterns = [
    path("lead-form/", views.lead_form, name="lead_form"),
    path("dashboard/", views.dashboard_home, name="dashboard_home"),
    path("dashboard/staff/", views.dashboard, name="dashboard"),
    path("dashboard/customer/", views.customer_dashboard, name="customer_dashboard"),
]
