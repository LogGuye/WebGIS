from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import Point
from django.db.models import Avg, Count
from django.shortcuts import redirect, render

from accounts.models import Agent, UserProfile
from accounts.permissions import role_required
from core.gis_tools import tool_assign_lead_to_nearest_agent
from properties.models import Property
from .models import Appointment, Lead


@role_required(UserProfile.Role.AGENT, UserProfile.Role.ADMIN)
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
                    pipeline_stage=Lead.PipelineStage.NEW,
                )
                agent, distance_km = tool_assign_lead_to_nearest_agent(point)
                if request.user.profile.role == UserProfile.Role.AGENT and request.user.profile.linked_agent:
                    lead_obj.assigned_agent = request.user.profile.linked_agent
                    lead_obj.save(update_fields=["assigned_agent"])
                    assignment = {"agent": lead_obj.assigned_agent, "distance": 0}
                    messages.success(request, "Khách hàng đã được gán cho môi giới hiện tại.")
                elif agent:
                    lead_obj.assigned_agent = agent
                    lead_obj.save(update_fields=["assigned_agent"])
                    assignment = {"agent": agent, "distance": round(distance_km, 2)}
                    messages.success(request, "Khách hàng đã được phân phối cho môi giới gần nhất.")
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
    appointment_qs = Appointment.objects.select_related("lead", "property", "agent")
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", UserProfile.Role.USER)
    linked_agent = getattr(profile, "linked_agent", None)

    if role == UserProfile.Role.AGENT and linked_agent:
        property_qs = property_qs.filter(agent=linked_agent)
        lead_qs = lead_qs.filter(assigned_agent=linked_agent)
        appointment_qs = appointment_qs.filter(agent=linked_agent)

    property_status = {
        row["listing_status"]: row["total"]
        for row in property_qs.values("listing_status").annotate(total=Count("id"))
    }
    property_types = property_qs.values("property_type").annotate(total=Count("id")).order_by("property_type")
    active_qs = property_qs.filter(listing_status=Property.ListingStatus.ACTIVE)
    avg_price_by_type = active_qs.values("property_type").annotate(avg_price=Avg("price"), avg_area=Avg("area"), total=Count("id")).order_by("property_type")
    pipeline_summary = {
        row["pipeline_stage"]: row["total"]
        for row in lead_qs.values("pipeline_stage").annotate(total=Count("id"))
    }

    if role == UserProfile.Role.ADMIN:
        pending_tasks = [
            ("Lead mới", lead_qs.filter(pipeline_stage=Lead.PipelineStage.NEW).count()),
            ("Tin chờ duyệt", property_qs.filter(listing_status=Property.ListingStatus.PENDING).count()),
            ("Tin đang ẩn", property_qs.filter(listing_status=Property.ListingStatus.HIDDEN).count()),
            ("Môi giới đang hoạt động", Agent.objects.count()),
        ]
        dashboard_note = "Bạn đang xem toàn bộ hệ thống: hàng tồn, lead, môi giới và hiệu suất chung."
        dashboard_actions = [
            ("/admin/properties/property/add/", "Thêm bất động sản"),
            ("/admin/properties/property/", "Quản lý bất động sản"),
            ("/admin/leads/lead/", "Quản lý khách hàng"),
            ("/admin/leads/appointment/", "Quản lý lịch hẹn"),
            ("/admin/accounts/agent/", "Quản lý môi giới"),
        ]
    else:
        pending_tasks = [
            ("Lead mới", lead_qs.filter(pipeline_stage=Lead.PipelineStage.NEW).count()),
            ("Đang tư vấn", lead_qs.filter(pipeline_stage=Lead.PipelineStage.CONSULTING).count()),
            ("Tin chờ duyệt", property_qs.filter(listing_status=Property.ListingStatus.PENDING).count()),
            ("Tin đang bán", property_qs.filter(listing_status=Property.ListingStatus.ACTIVE).count()),
        ]
        dashboard_note = "Bạn đang xem khu vực làm việc cá nhân: lead phụ trách, nguồn hàng và tình trạng tin đăng của mình."
        dashboard_actions = [
            ("/properties/create/", "Đăng tin mới"),
            ("/leads/lead-form/", "Tạo khách hàng"),
            ("/accounts/profile/", "Hồ sơ môi giới"),
        ]

    context = {
        "dashboard_role": role,
        "linked_agent": linked_agent,
        "dashboard_note": dashboard_note,
        "pending_tasks": pending_tasks,
        "dashboard_actions": dashboard_actions,
        "pipeline_summary": pipeline_summary,
        "property_total": property_qs.count(),
        "active_total": property_status.get("active", 0),
        "pending_total": property_status.get("pending", 0),
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
        "upcoming_appointments": appointment_qs.order_by("scheduled_at")[:5],
    }
    return render(request, "leads/dashboard.html", context)


@role_required(UserProfile.Role.AGENT, UserProfile.Role.ADMIN)
def lead_stage_update(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", None)
    linked_agent = getattr(profile, "linked_agent", None)

    if role == UserProfile.Role.AGENT and (not linked_agent or lead.assigned_agent_id != linked_agent.id):
        messages.error(request, "Bạn không có quyền cập nhật lead này.")
        return redirect("leads:dashboard")

    if request.method == "POST":
        next_stage = request.POST.get("pipeline_stage")
        allowed = {choice[0] for choice in Lead.PipelineStage.choices}
        if next_stage in allowed:
            lead.pipeline_stage = next_stage
            lead.save(update_fields=["pipeline_stage"])
            messages.success(request, f"Đã cập nhật lead sang trạng thái: {lead.get_pipeline_stage_display()}.")
        else:
            messages.error(request, "Trạng thái lead không hợp lệ.")
    return redirect("leads:dashboard")


@role_required(UserProfile.Role.AGENT, UserProfile.Role.ADMIN)
def appointment_create(request):
    profile = getattr(request.user, "profile", None)
    role = getattr(profile, "role", None)
    linked_agent = getattr(profile, "linked_agent", None)
    form = AppointmentCreateForm(request.POST or None, role=role, linked_agent=linked_agent)

    if request.method == "POST":
        if role == UserProfile.Role.AGENT and not linked_agent:
            messages.error(request, "Tài khoản môi giới chưa được gắn với hồ sơ môi giới nên chưa thể tạo lịch hẹn.")
        elif form.is_valid():
            appointment = form.save(commit=False)
            if role == UserProfile.Role.AGENT:
                appointment.agent = linked_agent
            elif not appointment.agent_id:
                appointment.agent = appointment.lead.assigned_agent or linked_agent
            appointment.save()
            if appointment.lead.pipeline_stage != Lead.PipelineStage.VIEWING:
                appointment.lead.pipeline_stage = Lead.PipelineStage.VIEWING
                appointment.lead.save(update_fields=["pipeline_stage"])
            messages.success(request, "Đã tạo lịch hẹn xem nhà.")
            return redirect("leads:dashboard")
        else:
            messages.error(request, "Vui lòng kiểm tra lại thông tin lịch hẹn.")

    return render(request, "leads/appointment_create.html", {"form": form})
