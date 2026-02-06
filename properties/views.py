from django.contrib.gis.geos import Point
from django.shortcuts import get_object_or_404, render

from core.gis_tools import tool_amenities_within_radius, tool_nearby_properties
from .models import Amenity, Property


def property_list(request):
    qs = Property.objects.select_related("agent").prefetch_related("amenities").all()
    prop_type = request.GET.get("type")
    price_min = request.GET.get("price_min")
    price_max = request.GET.get("price_max")
    area_min = request.GET.get("area_min")
    area_max = request.GET.get("area_max")

    if prop_type:
        qs = qs.filter(property_type=prop_type)
    if price_min:
        qs = qs.filter(price__gte=price_min)
    if price_max:
        qs = qs.filter(price__lte=price_max)
    if area_min:
        qs = qs.filter(area__gte=area_min)
    if area_max:
        qs = qs.filter(area__lte=area_max)

    context = {
        "properties": qs,
        "filters": {
            "type": prop_type or "",
            "price_min": price_min or "",
            "price_max": price_max or "",
            "area_min": area_min or "",
            "area_max": area_max or "",
        },
    }
    return render(request, "properties/property_list.html", context)


def property_detail(request, pk):
    prop = get_object_or_404(Property.objects.select_related("agent").prefetch_related("amenities"), pk=pk)
    return render(request, "properties/property_detail.html", {"property": prop})


def nearby_search(request):
    results = None
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    radius = request.GET.get("radius") or 5
    prop_type = request.GET.get("type") or ""

    if lat and lng:
        try:
            lat_f, lng_f, radius_f = float(lat), float(lng), float(radius)
            results = tool_nearby_properties(
                lat_f,
                lng_f,
                radius_f,
                filters={"property_type": prop_type or None},
            )
        except ValueError:
            results = []

    context = {
        "results": results,
        "params": {"lat": lat or "", "lng": lng or "", "radius": radius, "type": prop_type},
    }
    return render(request, "properties/nearby_search.html", context)


def amenity_search(request):
    results = None
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    radius = request.GET.get("radius") or 3
    amenity_type = request.GET.get("amenity_type") or ""

    if lat and lng:
        try:
            lat_f, lng_f, radius_f = float(lat), float(lng), float(radius)
            results = tool_amenities_within_radius(lat_f, lng_f, radius_f, amenity_type or None)
        except ValueError:
            results = []

    context = {
        "results": results,
        "amenity_types": Amenity.AmenityType.choices,
        "params": {"lat": lat or "", "lng": lng or "", "radius": radius, "amenity_type": amenity_type},
    }
    return render(request, "properties/amenity_search.html", context)
