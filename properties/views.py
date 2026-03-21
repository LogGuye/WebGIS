from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import Polygon
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import UserProfile
from accounts.permissions import role_required
from core.gis_tools import (
    tool_amenities_within_radius,
    tool_location_score,
    tool_nearby_properties,
    tool_similar_properties,
)
from .forms import PropertyCreateForm
from .image_forms import PropertyImageOrderForm, PropertyImageUploadForm
from .models import Amenity, Property, PropertyImage, SavedSearch


SORT_OPTIONS = {
    "default": "title",
    "price_asc": "price",
    "price_desc": "-price",
    "area_asc": "area",
    "area_desc": "-area",
    "newest": "-created_at",
}


def _viewer_role(request):
    if request.user.is_authenticated and hasattr(request.user, "profile"):
        return request.user.profile.role
    return None


def _viewer_agent(request):
    if request.user.is_authenticated and hasattr(request.user, "profile"):
        return request.user.profile.linked_agent
    return None


def _base_property_queryset(request):
    qs = Property.objects.select_related("agent").prefetch_related("amenities", "images").all()
    role = _viewer_role(request)
    linked_agent = _viewer_agent(request)
    if role == UserProfile.Role.AGENT and linked_agent:
        qs = qs.filter(agent=linked_agent)
    elif role != UserProfile.Role.ADMIN:
        qs = qs.filter(listing_status=Property.ListingStatus.ACTIVE)
    return qs


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
    qs, filters = _apply_property_filters(request, _base_property_queryset(request))
    paginator = Paginator(qs, 9)
    page_obj = paginator.get_page(request.GET.get("page") or 1)
    saved_searches = SavedSearch.objects.filter(user=request.user)[:5] if request.user.is_authenticated else []

    context = {
        "properties": page_obj.object_list,
        "page_obj": page_obj,
        "is_paginated": page_obj.has_other_pages(),
        "filters": filters,
        "property_types": Property.PropertyType.choices,
        "listing_statuses": Property.ListingStatus.choices,
        "total_count": paginator.count,
        "map_properties": list(qs[:300].values("id", "title", "price", "area", "address", "property_type", "location")),
        "heatmap_points": [[prop.location.y, prop.location.x, float(prop.price or 0)] for prop in qs[:300] if prop.location],
        "saved_searches": saved_searches,
    }
    return render(request, "properties/property_list.html", context)


def property_map_data(request):
    qs, _filters = _apply_property_filters(request, _base_property_queryset(request))
    items = []
    for prop in qs[:500]:
        if not prop.location:
            continue
        items.append({
            "id": prop.pk,
            "title": prop.title,
            "price": float(prop.price) if prop.price is not None else None,
            "area": prop.area,
            "address": prop.address,
            "property_type": prop.get_property_type_display(),
            "lat": prop.location.y,
            "lng": prop.location.x,
            "detail_url": f"/properties/{prop.pk}/",
        })
    return JsonResponse({"results": items})


def _get_session_ids(request, key):
    return request.session.get(key, [])


def _save_session_ids(request, key, ids):
    request.session[key] = ids
    request.session.modified = True


@login_required
def saved_search_create(request):
    if request.method == "POST":
        name = (request.POST.get("name") or "").strip() or "Bộ lọc đã lưu"
        SavedSearch.objects.create(
            user=request.user,
            name=name,
            query=(request.POST.get("q") or "").strip(),
            property_type=request.POST.get("type") or "",
            listing_status=request.POST.get("status") or "",
            price_min=request.POST.get("price_min") or None,
            price_max=request.POST.get("price_max") or None,
            area_min=request.POST.get("area_min") or None,
            area_max=request.POST.get("area_max") or None,
            alerts_enabled=True,
        )
        messages.success(request, "Đã lưu bộ tìm kiếm.")
    return redirect(request.META.get("HTTP_REFERER") or "properties:list")


@login_required
def saved_search_delete(request, pk):
    search = get_object_or_404(SavedSearch, pk=pk, user=request.user)
    search.delete()
    messages.success(request, "Đã xóa bộ tìm kiếm đã lưu.")
    return redirect(request.META.get("HTTP_REFERER") or "properties:list")


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
    role = _viewer_role(request)
    linked_agent = _viewer_agent(request)
    if prop.listing_status != Property.ListingStatus.ACTIVE:
        is_admin = role == UserProfile.Role.ADMIN
        is_owner_agent = role == UserProfile.Role.AGENT and linked_agent and prop.agent_id == linked_agent.id
        if not (is_admin or is_owner_agent):
            return redirect("properties:list")

    similar_properties = tool_similar_properties(prop, limit=4)
    location_score = tool_location_score(prop)
    wishlist_ids = [int(i) for i in _get_session_ids(request, "wishlist")]
    compare_ids = [int(i) for i in _get_session_ids(request, "compare")]
    return render(request, "properties/property_detail.html", {
        "property": prop,
        "similar_properties": similar_properties,
        "location_score": location_score,
        "is_in_wishlist": prop.pk in wishlist_ids,
        "is_in_compare": prop.pk in compare_ids,
    })


def nearby_search(request):
    results = None
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    radius = request.GET.get("radius") or 5
    prop_type = request.GET.get("type") or ""
    if lat and lng:
        try:
            results = tool_nearby_properties(float(lat), float(lng), float(radius), filters={"property_type": prop_type or None})
        except ValueError:
            results = []
    return render(request, "properties/nearby_search.html", {"results": results, "params": {"lat": lat or "", "lng": lng or "", "radius": radius, "type": prop_type}})


def amenity_search(request):
    results = None
    lat = request.GET.get("lat")
    lng = request.GET.get("lng")
    radius = request.GET.get("radius") or 3
    amenity_type = request.GET.get("amenity_type") or ""
    if lat and lng:
        try:
            results = tool_amenities_within_radius(float(lat), float(lng), float(radius), amenity_type or None)
        except ValueError:
            results = []
    return render(request, "properties/amenity_search.html", {"results": results, "amenity_types": Amenity.AmenityType.choices, "params": {"lat": lat or "", "lng": lng or "", "radius": radius, "amenity_type": amenity_type}})


@role_required(UserProfile.Role.AGENT, UserProfile.Role.ADMIN)
def property_create(request):
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", None)
    linked_agent = getattr(profile, "linked_agent", None)
    form = PropertyCreateForm(request.POST or None, user_role=role)

    if request.method == "POST":
        if role == UserProfile.Role.AGENT and not linked_agent:
            messages.error(request, "Tài khoản môi giới chưa được gắn với hồ sơ môi giới nên chưa thể đăng tin.")
        elif form.is_valid():
            listing_status = Property.ListingStatus.PENDING if role == UserProfile.Role.AGENT else form.cleaned_data.get("listing_status", Property.ListingStatus.ACTIVE)
            prop = form.save(agent=linked_agent, listing_status=listing_status)
            upload_files = request.FILES.getlist("images")
            for idx, uploaded in enumerate(upload_files):
                PropertyImage.objects.create(
                    property=prop,
                    image=uploaded,
                    caption=prop.title,
                    is_primary=(idx == 0),
                    sort_order=idx,
                )
            if role == UserProfile.Role.AGENT:
                messages.success(request, "Đăng tin thành công. Tin của bạn đang ở trạng thái chờ duyệt." + (" Ảnh đã được tải lên." if upload_files else ""))
            else:
                messages.success(request, "Đăng tin thành công." + (" Ảnh đã được tải lên." if upload_files else ""))
            return redirect("properties:detail", pk=prop.pk)
        else:
            messages.error(request, "Vui lòng kiểm tra lại thông tin đăng tin.")

    return render(request, "properties/property_create.html", {"form": form})
erty_images_manage(request, pk):
    prop = get_object_or_404(Property.objects.prefetch_related("images"), pk=pk)
    if not _can_manage_property(request, prop):
        messages.error(request, "Bạn không có quyền quản lý ảnh của tin này.")
        return redirect("properties:list")

    upload_form = PropertyImageUploadForm()
    order_forms = {img.pk: PropertyImageOrderForm(instance=img, prefix=f"img-{img.pk}") for img in prop.images.all()}
    return render(request, "properties/property_images_manage.html", {
        "property": prop,
        "upload_form": upload_form,
        "order_forms": order_forms,
    })


@role_required(UserProfile.Role.AGENT, UserProfile.Role.ADMIN)
def property_images_upload(request, pk):
    prop = get_object_or_404(Property.objects.prefetch_related("images"), pk=pk)
    if not _can_manage_property(request, prop):
        messages.error(request, "Bạn không có quyền tải ảnh cho tin này.")
        return redirect("properties:list")
    if request.method == "POST":
        files = request.FILES.getlist("images")
        start = prop.images.count()
        for idx, uploaded in enumerate(files):
            PropertyImage.objects.create(property=prop, image=uploaded, caption=prop.title, is_primary=(start == 0 and idx == 0), sort_order=start + idx)
        messages.success(request, f"Đã tải lên {len(files)} ảnh.")
    return redirect("properties:images_manage", pk=prop.pk)


@role_required(UserProfile.Role.AGENT, UserProfile.Role.ADMIN)
def property_image_set_primary(request, image_id):
    image = get_object_or_404(PropertyImage.objects.select_related("property"), pk=image_id)
    prop = image.property
    if not _can_manage_property(request, prop):
        messages.error(request, "Bạn không có quyền cập nhật ảnh của tin này.")
        return redirect("properties:list")
    prop.images.update(is_primary=False)
    image.is_primary = True
    image.save(update_fields=["is_primary"])
    messages.success(request, "Đã đặt ảnh chính.")
    return redirect("properties:images_manage", pk=prop.pk)


@role_required(UserProfile.Role.AGENT, UserProfile.Role.ADMIN)
def property_image_delete(request, image_id):
    image = get_object_or_404(PropertyImage.objects.select_related("property"), pk=image_id)
    prop = image.property
    if not _can_manage_property(request, prop):
        messages.error(request, "Bạn không có quyền xóa ảnh của tin này.")
        return redirect("properties:list")
    was_primary = image.is_primary
    image.delete()
    if was_primary:
        replacement = prop.images.order_by("sort_order", "id").first()
        if replacement:
            replacement.is_primary = True
            replacement.save(update_fields=["is_primary"])
    messages.success(request, "Đã xóa ảnh.")
    return redirect("properties:images_manage", pk=prop.pk)


@role_required(UserProfile.Role.AGENT, UserProfile.Role.ADMIN)
def property_image_reorder(request, image_id):
    image = get_object_or_404(PropertyImage.objects.select_related("property"), pk=image_id)
    prop = image.property
    if not _can_manage_property(request, prop):
        messages.error(request, "Bạn không có quyền sắp xếp ảnh của tin này.")
        return redirect("properties:list")
    if request.method == "POST":
        try:
            image.sort_order = int(request.POST.get("sort_order", image.sort_order))
            image.save(update_fields=["sort_order"])
            messages.success(request, "Đã cập nhật thứ tự ảnh.")
        except ValueError:
            messages.error(request, "Thứ tự ảnh không hợp lệ.")
    return redirect("properties:images_manage", pk=prop.pk)
