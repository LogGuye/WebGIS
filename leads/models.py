from django.contrib.gis.db import models
from django.utils import timezone

from accounts.models import Agent
from properties.models import Property


class Lead(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    budget = models.DecimalField(max_digits=14, decimal_places=2)
    desired_location = models.PointField(geography=True, srid=4326)
    assigned_agent = models.ForeignKey(Agent, on_delete=models.SET_NULL, null=True, blank=True, related_name="leads")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.phone})"


class Appointment(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="appointments")
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="appointments")
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="appointments")
    scheduled_at = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-scheduled_at"]

    def __str__(self):
        return f"Appointment for {self.lead} at {self.property}"
