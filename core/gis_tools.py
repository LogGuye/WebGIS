from django.contrib.gis.geos import Point
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance

from accounts.models import Agent
from properties.models import Amenity, Property


def _point_from_lat_lng(lat: float, lng: float) -> Point:
    """Helper to build Point from lat/lng using WGS84."""
    return Point(lng, lat, srid=4326)


def tool_nearby_properties(lat, lng, radius_km, filters=None):
    """
    Return queryset of properties within radius_km of lat/lng.
    Filters dict keys: property_type, price_min, price_max, area_min, area_max.
    Annotates distance in km and orders ascending.
    """
    filters = filters or {}
    ref_point = _point_from_lat_lng(lat, lng)
    qs = Property.objects.annotate(distance=Distance("location", ref_point)).filter(location__distance_lte=(ref_point, D(km=radius_km)))

    if filters.get("property_type"):
        qs = qs.filter(property_type=filters["property_type"])
    if filters.get("price_min") is not None:
        qs = qs.filter(price__gte=filters["price_min"])
    if filters.get("price_max") is not None:
        qs = qs.filter(price__lte=filters["price_max"])
    if filters.get("area_min") is not None:
        qs = qs.filter(area__gte=filters["area_min"])
    if filters.get("area_max") is not None:
        qs = qs.filter(area__lte=filters["area_max"])

    return qs.order_by("distance")


def tool_assign_lead_to_nearest_agent(lead_location: Point):
    """
    Find nearest agent to given Point.
    Returns (agent, distance_km) or (None, None) if no agent.
    """
    qs = (
        Agent.objects.annotate(distance=Distance("location", lead_location))
        .order_by("distance")
    )
    agent = qs.first()
    if not agent:
        return None, None
    return agent, agent.distance.km


def tool_amenities_within_radius(lat, lng, radius_km, amenity_type=None):
    """
    Return amenities within radius_km of lat/lng, optionally filtered by amenity_type.
    Annotates distance in km and orders ascending.
    """
    ref_point = _point_from_lat_lng(lat, lng)
    qs = Amenity.objects.annotate(distance=Distance("location", ref_point)).filter(
        location__distance_lte=(ref_point, D(km=radius_km))
    )
    if amenity_type:
        qs = qs.filter(amenity_type=amenity_type)
    return qs.order_by("distance")
