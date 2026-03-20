from django.shortcuts import render

from accounts.models import Agent
from leads.models import Lead
from properties.models import Amenity, Property


def home(request):
    featured_properties = Property.objects.filter(listing_status="active", is_featured=True).prefetch_related("images")[:3]
    context = {
        "property_count": Property.objects.count(),
        "agent_count": Agent.objects.count(),
        "lead_count": Lead.objects.count(),
        "amenity_count": Amenity.objects.count(),
        "featured_properties": featured_properties,
        "wishlist_count": len(request.session.get("wishlist", [])),
        "compare_count": len(request.session.get("compare", [])),
    }
    return render(request, "core/home.html", context)
