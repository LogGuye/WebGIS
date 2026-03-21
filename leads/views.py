from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import Point
from django.db.models import Avg, Count, Q
from django.shortcuts import redirect, render

from accounts.models import Agent, UserProfile
from accounts.permissions import role_required
from core.gis_tools import tool_assign_lead_to_nearest_agent
from properties.models import Property
from .models import Lead


@login_required
def lead_form(request):
    assignment = None
    lead_obj = None
    if request.method == "POST":
        name = request.POST.get("name")
        phone = request.POST.get("phone")
        budget = request.POST.get("budget")
        lat = request.POST.get("lat")
        lng = request.POST.get("lng")
        property_interest = request.POST.get("property_interest") or request.POST.get("property", "")
        notes = request.POST.get("notes", "")
        alert_enabled = request.POST.get("alert_enabled") == "on"

        if name and phone and budget and lat and lng:
            try:
                point = Point(float(lng), float(lat), srid=4326)
                lead_obj = Lead.objects.create(
                    name=name,
                    phone=phone,
                    budget=budget,
                    desired_location=point,
                    property_interest=property_interest,
                    notes=notes,
                    alert_enabled=alert_enabled,
                )
                agent, distance_km = tool_assign_lead_to_nearest_agent(point)
                if request.user.is_authenticated and hasattr(request.user, "profile") and request.user.profile.role == UserProfile.Role.AGENT and request.user.profile.linked_agent:
                    lead_obj.assigned_agent = request.user.profile.linked_agent
                    lead_obj.save(update_fields=["assigned_agent"])
                    assignment = {"agent": lead_obj.assigned_agent, "distance": 0}
                    messages.success(request, "Lead đã được gán cho môi giới hiện tại.")
                elif agent:
                    lead_obj.assigned_agent = agent
                    lead_obj.save(update_fields=["assigned_agent"])
                    assignment = {"agent": agent, "distance": round(distance_km, 2)}
                    messages.success(request, "Lead đã được phân phối cho môi giới gần nhất.")
                else:
                    messages.warning(request, "Chưa có môi giới nào trong hệ thống.")
            except ValueError:
                messages.error(request, "Vui lòng nhập tọa độ hợp lệ.")
        else:
            messages.error(request, "Vui lòng điền đầy đủ thông tin.")

    context = {"assignment": assignment, "lead": lead_obj, "agents": Agent.objects.count()}
    return render(request, "leads/lead_form.html", context)


@login_required
def dashboard_home(request):
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", UserProfile.Role.USER)
    if role in (UserProfile.Role.AGENT, UserProfile.Role.ADMIN):
        return redirect("leads:dashboard")
    return customer_dashboard(request)


@login_required
def customer_dashboard(request):
    wishlist_ids = request.session.get("wishlist", [])
    compare_ids = request.session.get("compare", [])
    wishlist_qs = Property.objects.filter(pk__in=wishlist_ids).select_related("agent").prefetch_related("images")
    compare_qs = Property.objects.filter(pk__in=compare_ids).select_related("agent").prefetch_related("images")
    recommended = Property.objects.filter(listing_status=Property.ListingStatus.ACTIVE, is_featured=True).select_related("agent").prefetch_related("images")[:6]

    context = {
        "wishlist_properties": wishlist_qs[:3],
        "compare_properties": compare_qs[:3],
        "recommended_properties": recommended,
        "wishlist_total": wishlist_qs.count(),
        "compare_total": compare_qs.count(),
        "featured_total": Property.objects.filter(listing_status=Property.ListingStatus.ACTIVE, is_featured=True).count(),
        "active_total": Property.objects.filter(listing_status=Property.ListingStatus.ACTIVE).count(),
    }
    return render(request, "leads/customer_dashboard.html", context)


@role_required(UserProfile.Role.AGENT, UserProfile.Role.ADMIN)
def dashboard(request):
    property_qs = Property.objects.all()
    lead_qs = Lead.objects.all()
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", UserProfile.Role.USER)
    linked_agent = getattr(profile, "linked_agent", None)

    if role == UserProfile.Role.AGENT and linked_agent:
        property_qs = property_qs.filter(agent=linked_agent)
        lead_qs = lead_qs.filter(assigned_agent=linked_agent)

    property_status = {
        row["listing_status"]: row["total"]
        for row in property_qs.values("listing_status").annotate(total=Count("id"))
    }
    property_types = property_qs.values("property_type").annotate(total=Count("id")).order_by("property_type")
    active_qs = property_qs.filter(listing_status=Property.ListingStatus.ACTIVE)
    avg_price_by_type = active_qs.values("property_type").annotate(avg_price=Avg("price"), avg_area=Avg("area"), total=Count("id")).order_by("property_type")

    if role == UserProfile.Role.ADMIN:
        pending_tasks = [
            ("Lead chưa bật cảnh báo", lead_qs.filter(alert_enabled=False).count()),
            ("Tin đang ẩn", property_qs.filter(listing_status=Property.ListingStatus.HIDDEN).count()),
            ("Tin nổi bật đang chạy", property_qs.filter(is_featured=True, listing_status=Property.ListingStatus.ACTIVE).count()),
            ("Môi giới đang hoạt động", Agent.objects.count()),
        ]
        dashboard_note = "Bạn đang xem toàn bộ hệ thống: hàng tồn, lead, môi giới và hiệu suất chung."
        dashboard_actions = [
            ("/admin/", "Quản trị hệ thống"),
            ("/accounts/profile/", "Quản lý hồ sơ"),
        ]
    else:
        pending_tasks = [
            ("Lead cần theo dõi", lead_qs.count()),
            ("Lead bật cảnh báo", lead_qs.filter(alert_enabled=True).count()),
            ("Tin đang bán của bạn", property_qs.filter(listing_status=Property.ListingStatus.ACTIVE).count()),
            ("Tin nổi bật bạn đang phụ trách", property_qs.filter(is_featured=True, listing_status=Property.ListingStatus.ACTIVE).count()),
        ]
        dashboard_note = "Bạn đang xem khu vực làm việc cá nhân: lead phụ trách, nguồn hàng và tình trạng tin đăng của mình."
        dashboard_actions = [
            ("/leads/lead-form/", "Tạo khách hàng mới"),
            ("/accounts/profile/", "Hồ sơ môi giới"),
        ]

    context = {
        "dashboard_role": role,
        "linked_agent": linked_agent,
        "dashboard_note": dashboard_note,
        "pending_tasks": pending_tasks,
        "property_total": property_qs.count(),
        "active_total": property_status.get("active", 0),
        "sold_total": property_status.get("sold", 0),
        "hidden_total": property_status.get("hidden", 0),
        "featured_total": property_qs.filter(is_featured=True).count(),
        "lead_total": lead_qs.count(),
        "alert_total": lead_qs.filter(alert_enabled=True).count(),
        "agent_total": Agent.objects.count(),
        "property_types": property_types,
        "avg_price_by_type": avg_price_by_type,
        "avg_price_all": active_qs.aggregate(avg=Avg("price")).get("avg"),
        "avg_area_all": active_qs.aggregate(avg=Avg("area")).get("avg"),
        "recent_leads": lead_qs.select_related("assigned_agent").order_by("-created_at")[:5],
    }
    return render(request, "leads/dashboard.html", context)
