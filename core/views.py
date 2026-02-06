from django.shortcuts import render

from accounts.models import Agent
from leads.models import Lead
from properties.models import Amenity, Property


def home(request):
    context = {
        "property_count": Property.objects.count(),
        "agent_count": Agent.objects.count(),
        "lead_count": Lead.objects.count(),
        "amenity_count": Amenity.objects.count(),
    }
    return render(request, "core/home.html", context)
