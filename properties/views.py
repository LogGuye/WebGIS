from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import Point, Polygon
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import UserProfile

from core.gis_tools import (
    tool_amenities_within_radius,
    tool_location_score,
    tool_nearby_properties,
    tool_similar_properties,
)
from .models import Amenity, Property


SORT_OPTIONS = {
    "default": "title",
    "price_asc": "price",
    "price_desc": "-price",
    "area_asc": "area",
    "area_desc": "-area",
    "newest": "-created_at",
}


def _parse_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _apply_property_filters(request, queryset):
    prop_type = request.GET.get("type")
    listing_status = request.GET.get("status") or "active"
    price_min = request.GET.get("price_min")
    price_max = request.GET.get("price_max")
    area_min = request.GET.get("area_min")
    area_max = request.GET.get("area_max")
    q = (request.GET.get("q") or "").strip()
    sort = request.GET.get("sort") or "default"
    bbox = (request.GET.get("bbox") or "").strip()

    if prop_type:
        queryset = queryset.filter(property_type=prop_type)
    if listing_status:
        queryset = queryset.filter(listing_status=listing_status)
    if price_min:
        queryset = queryset.filter(price__gte=price_min)
    if price_max:
        queryset = queryset.filter(price__lte=price_max)
    if area_min:
        queryset = queryset.filter(area__gte=area_min)
    if area_max:
        queryset = queryset.filter(area__lte=area_max)
    if q:
        queryset = queryset.filter(
            Q(title__icontains=q)
            | Q(address__icontains=q)
            | Q(description__icontains=q)
            | Q(agent__name__icontains=q)
        )

    if bbox:
        try:
            min_lng, min_lat, max_lng, max_lat = [float(v) for v in bbox.split(",")]
            envelope = Polygon.from_bbox((min_lng, min_lat, max_lng, max_lat))
            envelope.srid = 4326
            queryset = queryset.filter(location__within=envelope)
        except (TypeError, ValueError):
            pass

    queryset = queryset.order_by(SORT_OPTIONS.get(sort, "title"))

    filters = {
        "type": prop_type or "",
        "status": listing_status or "",
        "price_min": price_min or "",
        "price_max": price_max or "",
        "area_min": area_min or "",
        "area_max": area_max or "",
        "q": q,
        "sort": sort,
        "bbox": bbox,
    }
    return queryset, filters


def property_list(request):
    qs = Property.objects.select_related("agent").prefetch_related("amenities", "images").all()
    if request.user.is_authenticated and hasattr(request.user, "profile") and request.user.profile.role == UserProfile.Role.AGENT and request.user.profile.linked_agent:
        qs = qs.filter(agent=request.user.profile.linked_agent)
    qs, filters = _apply_property_filters(request, qs)

    paginator = Paginator(qs, 9)
    page_obj = paginator.get_page(request.GET.get("page") or 1)

    context = {
        "properties": page_obj.object_list,
        "page_obj": page_obj,
        "is_paginated": page_obj.has_other_pages(),
        "filters": filters,
        "property_types": Property.PropertyType.choices,
        "listing_statuses": Property.ListingStatus.choices,
        "total_count": paginator.count,
        "map_properties": list(
            qs[:300].values(
                "id",
                "title",
                "price",
                "area",
                "address",
                "property_type",
                "location",
            )
        ),
        "heatmap_points": [
            [prop.location.y, prop.location.x, float(prop.price or 0)]
            for prop in qs[:300]
            if prop.location
        ],
    }
    return render(request, "properties/property_list.html", context)


def property_map_data(request):
    qs = Property.objects.select_related("agent").prefetch_related("images").all()
    if request.user.is_authenticated and hasattr(request.user, "profile") and request.user.profile.role == UserProfile.Role.AGENT and request.user.profile.linked_agent:
        qs = qs.filter(agent=request.user.profile.linked_agent)
    qs, _filters = _apply_property_filters(request, qs)

    items = []
    for prop in qs[:500]:
        if not prop.location:
            continue
        items.append(
            {
                "id": prop.pk,
                "title": prop.title,
                "price": float(prop.price) if prop.price is not None else None,
                "area": prop.area,
                "address": prop.address,
                "property_type": prop.get_property_type_display(),
                "lat": prop.location.y,
                "lng": prop.location.x,
                "detail_url": request.build_absolute_uri(prop.get_absolute_url()) if hasattr(prop, "get_absolute_url") else f"/properties/{prop.pk}/",
            }
        )
    return JsonResponse({"results": items})


def _get_session_ids(request, key):
    return request.session.get(key, [])


def _save_session_ids(request, key, ids):
    request.session[key] = ids
    request.session.modified = True


@login_required
def wishlist_toggle(request, pk):
    ids = [int(i) for i in _get_session_ids(request, "wishlist")]
    if pk in ids:
        ids.remove(pk)
    else:
        ids.append(pk)
    _save_session_ids(request, "wishlist", ids)
    return redirect(request.META.get("HTTP_REFERER") or "properties:list")


@login_required
def wishlist_view(request):
    ids = _get_session_ids(request, "wishlist")
    properties = Property.objects.filter(pk__in=ids).prefetch_related("images")
    return render(request, "properties/wishlist.html", {"properties": properties})


@login_required
def compare_toggle(request, pk):
    ids = [int(i) for i in _get_session_ids(request, "compare")]
    if pk in ids:
        ids.remove(pk)
    elif len(ids) < 3:
        ids.append(pk)
    _save_session_ids(request, "compare", ids)
    return redirect(request.META.get("HTTP_REFERER") or "properties:list")


@login_required
def compare_view(request):
    ids = _get_session_ids(request, "compare")
    properties = list(Property.objects.filter(pk__in=ids).select_related("agent").prefetch_related("amenities"))
    return render(request, "properties/compare.html", {"properties": properties})


def property_detail(request, pk):
    prop = get_object_or_404(Property.objects.select_related("agent").prefetch_related("amenities", "images"), pk=pk)
    similar_properties = tool_similar_properties(prop, limit=4)
    location_score = tool_location_score(prop)
    wishlist_ids = [int(i) for i in _get_session_ids(request, "wishlist")]
    compare_ids = [int(i) for i in _get_session_ids(request, "compare")]
    return render(
        request,
        "properties/property_detail.html",
        {
            "property": prop,
            "similar_properties": similar_properties,
            "location_score": location_score,
            "is_in_wishlist": prop.pk in wishlist_ids,
            "is_in_compare": prop.pk in compare_ids,
        },
    )


def nearby_search(request):
    results = None
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    radius = request.GET.get("radius") or 5
    prop_type = request.GET.get("type") or ""
    location_query = request.GET.get("location_query") or ""

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
