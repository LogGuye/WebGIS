from django.contrib import messages
from django.contrib.gis.geos import Point
from django.db.models import Avg, Count
from django.shortcuts import render

from accounts.models import Agent
from core.gis_tools import tool_assign_lead_to_nearest_agent
from properties.models import Property
from .models import Lead


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
                if agent:
                    lead_obj.assigned_agent = agent
                    lead_obj.save(update_fields=["assigned_agent"])
                    assignment = {"agent": agent, "distance": round(distance_km, 2)}
                    messages.success(request, "Lead đã được phân phối cho agent gần nhất.")
                else:
                    messages.warning(request, "Chưa có agent nào trong hệ thống.")
            except ValueError:
                messages.error(request, "Vui lòng nhập tọa độ hợp lệ.")
        else:
            messages.error(request, "Vui lòng điền đầy đủ thông tin.")

    context = {"assignment": assignment, "lead": lead_obj, "agents": Agent.objects.count()}
    return render(request, "leads/lead_form.html", context)


def dashboard(request):
    property_status = {
        row["listing_status"]: row["total"]
        for row in Property.objects.values("listing_status").annotate(total=Count("id"))
    }
    property_types = Property.objects.values("property_type").annotate(total=Count("id")).order_by("property_type")
    active_qs = Property.objects.filter(listing_status=Property.ListingStatus.ACTIVE)
    avg_price_by_type = active_qs.values("property_type").annotate(avg_price=Avg("price"), avg_area=Avg("area"), total=Count("id")).order_by("property_type")
    context = {
        "property_total": Property.objects.count(),
        "active_total": property_status.get("active", 0),
        "sold_total": property_status.get("sold", 0),
        "hidden_total": property_status.get("hidden", 0),
        "featured_total": Property.objects.filter(is_featured=True).count(),
        "lead_total": Lead.objects.count(),
        "alert_total": Lead.objects.filter(alert_enabled=True).count(),
        "agent_total": Agent.objects.count(),
        "property_types": property_types,
        "avg_price_by_type": avg_price_by_type,
        "avg_price_all": active_qs.aggregate(avg=Avg("price")).get("avg"),
        "avg_area_all": active_qs.aggregate(avg=Avg("area")).get("avg"),
        "recent_leads": Lead.objects.select_related("assigned_agent").order_by("-created_at")[:5],
    }
    return render(request, "leads/dashboard.html", context)
