import json

from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.contrib.gis.geos import Point
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

from accounts.models import Agent, UserProfile
from accounts.permissions import role_required
from leads.models import Lead
from properties.models import Amenity, Property


def _parse_json_payload(request):
    try:
        payload = json.loads(request.body.decode() or "{}")
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _build_point(lat_value, lng_value):
    try:
        lat = float(lat_value)
        lng = float(lng_value)
    except (TypeError, ValueError):
        return None
    return Point(lng, lat, srid=4326)


def _serialize_agent(agent):
    location = agent.location
    return {
        "id": agent.id,
        "name": agent.name,
        "email": agent.email,
        "phone": agent.phone,
        "lat": location.y if location else None,
        "lng": location.x if location else None,
    }


def _serialize_amenity(amenity):
    location = amenity.location
    return {
        "id": amenity.id,
        "name": amenity.name,
        "amenity_type": amenity.amenity_type,
        "lat": location.y if location else None,
        "lng": location.x if location else None,
    }


def _serialize_lead(lead):
    location = lead.desired_location
    return {
        "id": lead.id,
        "name": lead.name,
        "phone": lead.phone,
        "budget": float(lead.budget) if lead.budget is not None else None,
        "property_interest": lead.property_interest,
        "pipeline_stage": lead.pipeline_stage,
        "assigned_agent": {
            "id": lead.assigned_agent.id,
            "name": lead.assigned_agent.name,
        } if lead.assigned_agent else None,
        "lat": location.y if location else None,
        "lng": location.x if location else None,
        "notes": lead.notes,
        "alert_enabled": lead.alert_enabled,
    }


def _serialize_property(prop):
    location = prop.location
    return {
        "id": prop.id,
        "title": prop.title,
        "description": prop.description,
        "property_type": prop.property_type,
        "listing_status": prop.listing_status,
        "price": float(prop.price) if prop.price is not None else None,
        "area": prop.area,
        "address": prop.address,
        "agent": {"id": prop.agent.id, "name": prop.agent.name} if prop.agent else None,
        "lat": location.y if location else None,
        "lng": location.x if location else None,
        "is_featured": prop.is_featured,
    }


def _apply_lead_payload(payload, lead=None):
    if lead is None:
        lead = Lead()
    lead.name = (payload.get("name") or "").strip()
    lead.phone = (payload.get("phone") or "").strip()
    try:
        lead.budget = Decimal(str(payload.get("budget")))
    except (InvalidOperation, ValueError, TypeError):
        lead.budget = None
    lead.property_interest = (payload.get("property_interest") or "").strip()
    point = _build_point(payload.get("lat"), payload.get("lng"))
    if point:
        lead.desired_location = point
    lead.notes = (payload.get("notes") or "").strip()
    lead.alert_enabled = bool(payload.get("alert_enabled"))
    pipeline = payload.get("pipeline_stage")
    if pipeline in {choice[0] for choice in Lead.PipelineStage.choices}:
        lead.pipeline_stage = pipeline
    agent_id = payload.get("assigned_agent_id")
    if agent_id:
        try:
            agent = Agent.objects.get(pk=int(agent_id))
        except (Agent.DoesNotExist, ValueError, TypeError):
            agent = None
    else:
        agent = None
    lead.assigned_agent = agent
    return lead


def _apply_agent_payload(payload, agent=None):
    if agent is None:
        agent = Agent()
    agent.name = (payload.get("name") or "").strip()
    agent.email = (payload.get("email") or "").strip()
    agent.phone = (payload.get("phone") or "").strip()
    point = _build_point(payload.get("lat"), payload.get("lng"))
    if point:
        agent.location = point
    return agent


def _apply_amenity_payload(payload, amenity=None):
    if amenity is None:
        amenity = Amenity()
    amenity.name = (payload.get("name") or "").strip()
    amenity_type = payload.get("amenity_type")
    if amenity_type in {choice[0] for choice in Amenity.AmenityType.choices}:
        amenity.amenity_type = amenity_type
    point = _build_point(payload.get("lat"), payload.get("lng"))
    if point:
        amenity.location = point
    return amenity


def _apply_property_payload(payload, prop=None):
    from decimal import Decimal

    if prop is None:
        prop = Property()
    prop.title = (payload.get("title") or "").strip()
    prop.description = (payload.get("description") or "").strip()
    prop.property_type = payload.get("property_type") or Property.PropertyType.APARTMENT
    prop.listing_status = payload.get("listing_status") or Property.ListingStatus.ACTIVE
    try:
        prop.price = Decimal(str(payload.get("price")))
    except (InvalidOperation, ValueError, TypeError):
        prop.price = None
    try:
        prop.area = float(payload.get("area"))
    except (TypeError, ValueError):
        prop.area = None
    prop.address = (payload.get("address") or "").strip()
    point = _build_point(payload.get("lat"), payload.get("lng"))
    if point:
        prop.location = point
    prop.is_featured = bool(payload.get("is_featured"))
    agent_id = payload.get("agent_id")
    if agent_id:
        try:
            agent = Agent.objects.get(pk=int(agent_id))
        except (Agent.DoesNotExist, ValueError, TypeError):
            agent = None
    else:
        agent = None
    prop.agent = agent
    return prop


@role_required(UserProfile.Role.ADMIN)
@require_http_methods(["GET", "POST"])
def admin_leads_collection(request):
    if request.method == "GET":
        leads = Lead.objects.select_related("assigned_agent").all()
        return JsonResponse({"results": [_serialize_lead(lead) for lead in leads]})
    payload = _parse_json_payload(request)
    if payload is None:
        return JsonResponse({"error": "JSON payload không hợp lệ."}, status=400)
    lead = _apply_lead_payload(payload)
    if not lead.name or not lead.phone:
        return JsonResponse({"error": "Tên và điện thoại bắt buộc."}, status=400)
    lead.save()
    return JsonResponse(_serialize_lead(lead), status=201)


@role_required(UserProfile.Role.ADMIN)
@require_http_methods(["GET", "PUT", "DELETE"])
def admin_lead_record(request, pk):
    lead = get_object_or_404(Lead, pk=pk)
    if request.method == "GET":
        return JsonResponse(_serialize_lead(lead))
    if request.method == "DELETE":
        lead.delete()
        return JsonResponse({}, status=204)
    payload = _parse_json_payload(request)
    if payload is None:
        return JsonResponse({"error": "JSON payload không hợp lệ."}, status=400)
    lead = _apply_lead_payload(payload, lead=lead)
    lead.save()
    return JsonResponse(_serialize_lead(lead))


@role_required(UserProfile.Role.ADMIN)
@require_http_methods(["GET", "POST"])
def admin_agents_collection(request):
    if request.method == "GET":
        agents = Agent.objects.all()
        return JsonResponse({"results": [_serialize_agent(agent) for agent in agents]})
    payload = _parse_json_payload(request)
    if payload is None:
        return JsonResponse({"error": "JSON payload không hợp lệ."}, status=400)
    agent = _apply_agent_payload(payload)
    if not agent.name or not agent.email:
        return JsonResponse({"error": "Tên và email bắt buộc."}, status=400)
    agent.save()
    return JsonResponse(_serialize_agent(agent), status=201)


@role_required(UserProfile.Role.ADMIN)
@require_http_methods(["GET", "PUT", "DELETE"])
def admin_agent_record(request, pk):
    agent = get_object_or_404(Agent, pk=pk)
    if request.method == "GET":
        return JsonResponse(_serialize_agent(agent))
    if request.method == "DELETE":
        agent.delete()
        return JsonResponse({}, status=204)
    payload = _parse_json_payload(request)
    if payload is None:
        return JsonResponse({"error": "JSON payload không hợp lệ."}, status=400)
    agent = _apply_agent_payload(payload, agent=agent)
    agent.save()
    return JsonResponse(_serialize_agent(agent))


@role_required(UserProfile.Role.ADMIN)
@require_http_methods(["GET", "POST"])
def admin_amenities_collection(request):
    if request.method == "GET":
        amenities = Amenity.objects.all()
        return JsonResponse({"results": [_serialize_amenity(a) for a in amenities]})
    payload = _parse_json_payload(request)
    if payload is None:
        return JsonResponse({"error": "JSON payload không hợp lệ."}, status=400)
    amenity = _apply_amenity_payload(payload)
    if not amenity.name:
        return JsonResponse({"error": "Tên tiện ích bắt buộc."}, status=400)
    amenity.save()
    return JsonResponse(_serialize_amenity(amenity), status=201)


@role_required(UserProfile.Role.ADMIN)
@require_http_methods(["GET", "PUT", "DELETE"])
def admin_amenity_record(request, pk):
    amenity = get_object_or_404(Amenity, pk=pk)
    if request.method == "GET":
        return JsonResponse(_serialize_amenity(amenity))
    if request.method == "DELETE":
        amenity.delete()
        return JsonResponse({}, status=204)
    payload = _parse_json_payload(request)
    if payload is None:
        return JsonResponse({"error": "JSON payload không hợp lệ."}, status=400)
    amenity = _apply_amenity_payload(payload, amenity=amenity)
    amenity.save()
    return JsonResponse(_serialize_amenity(amenity))
