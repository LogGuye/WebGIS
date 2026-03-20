from django.contrib.gis.geos import Point
from django.shortcuts import get_object_or_404, render
from django.core.serializers import serialize
from django.http import HttpResponse
from core.gis_tools import tool_amenities_within_radius, tool_nearby_properties
from .models import Amenity, Property
from django.http import JsonResponse
from django.contrib.gis.measure import D
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Polygon
from django.http import HttpResponse

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

# API Điểm tiện ích
def property_geojson(request):

    properties = Property.objects.all()
    data = serialize(
        'geojson', 
        properties, 
        geometry_field='location', 
        fields=('title', 'price', 'property_type', 'address')
    )
    return HttpResponse(data, content_type='application/json')

# API Điểm tiện ích
def property_amenity_stats(request, pk):
    prop = get_object_or_404(Property, pk=pk)
    
    lat = prop.location.y
    lng = prop.location.x
    radius_km = 1.0 
    
    stats = {}
    total_count = 0
    
    for choice_value, choice_label in Amenity.AmenityType.choices:
        amenities = tool_amenities_within_radius(lat, lng, radius_km, amenity_type=choice_value)
        count = len(amenities)
        stats[choice_value] = {
            "label": str(choice_label),
            "count": count
        }
        total_count += count

    return JsonResponse({
        "property_id": pk,
        "total_amenities": total_count,
        "breakdown": stats,
        "score": min(10, total_count) 
    })

# API Tìm kiếm BDS tương tự
def similar_properties_api(request, pk):
    try:
        base_prop = Property.objects.get(pk=pk)
    except Property.DoesNotExist:
        return JsonResponse({"error": "Property not found"}, status=404)

    min_price = float(base_prop.price) * 0.8
    max_price = float(base_prop.price) * 1.2

    similar_props = (
        Property.objects
        .exclude(pk=base_prop.pk)
        .filter(property_type=base_prop.property_type)
        .filter(price__gte=min_price, price__lte=max_price)
        .filter(location__distance_lte=(base_prop.location, D(km=5)))
        .annotate(distance=Distance('location', base_prop.location))
        .order_by('distance')[:5]
    )

    data = []
    for p in similar_props:
        data.append({
            "id": p.id,
            "title": p.title,
            "price": str(p.price),
            "area": p.area,
            "distance_km": round(p.distance.km, 2) 
        })

    return JsonResponse({
        "base_property_id": base_prop.id,
        "results": data
    })

# Bounding Box Search
def map_bounds_search_api(request):
    qs = Property.objects.select_related("agent").all()
    bbox_string = request.GET.get('bbox')
    
    if bbox_string:
        try:
            p1x, p1y, p2x, p2y = (float(n) for n in bbox_string.split(','))
            bbox_geom = Polygon.from_bbox((p1x, p1y, p2x, p2y))
            qs = qs.filter(location__within=bbox_geom)
        except ValueError:
            pass 

    prop_type = request.GET.get("type")
    price_max = request.GET.get("price_max")
    
    if prop_type:
        qs = qs.filter(property_type=prop_type)
    if price_max:
        qs = qs.filter(price__lte=price_max)

    data = serialize(
        'geojson', 
        qs, 
        geometry_field='location', 
        fields=('title', 'price', 'property_type', 'address', 'area')
    )
    return HttpResponse(data, content_type='application/json')

# Tiện ích gần nhất và đo khoảng cách
def property_nearest_amenities(request, pk):
    try:
        prop = Property.objects.get(pk=pk)
    except Property.DoesNotExist:
        return JsonResponse({"error": "Property not found"}, status=404)

    results = []

    for choice_value, choice_label in Amenity.AmenityType.choices:
        nearest = (
            Amenity.objects
            .filter(amenity_type=choice_value)
            .annotate(distance=Distance('location', prop.location))
            .order_by('distance')
            .first()
        )

        if nearest:
            dist_meters = nearest.distance.m
            
            if dist_meters >= 1000:
                dist_str = f"{round(dist_meters / 1000, 1)} km"
            else:
                dist_str = f"{int(dist_meters)} m"

            results.append({
                "type_code": choice_value,
                "type_label": str(choice_label),
                "name": nearest.name,
                "distance_value": dist_meters,
                "distance_display": dist_str
            })
    results = sorted(results, key=lambda x: x["distance_value"])

    return JsonResponse({
        "property_id": prop.id,
        "nearest_amenities": results
    })