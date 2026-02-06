from django.contrib import messages
from django.contrib.gis.geos import Point
from django.shortcuts import redirect, render

from accounts.models import Agent
from core.gis_tools import tool_assign_lead_to_nearest_agent
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

        if name and phone and budget and lat and lng:
            try:
                point = Point(float(lng), float(lat), srid=4326)
                lead_obj = Lead.objects.create(
                    name=name,
                    phone=phone,
                    budget=budget,
                    desired_location=point,
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
