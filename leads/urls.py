from django.urls import path

from . import views

urlpatterns = [
    path("lead-form/", views.lead_form, name="lead_form"),
]
