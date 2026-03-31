from django.shortcuts import render

from accounts.models import Agent, UserProfile
from accounts.permissions import role_required
from leads.models import Lead
from properties.models import Amenity, Property


def home(request):
    featured_properties = Property.objects.filter(listing_status="active", is_featured=True).prefetch_related("images")[:3]
    context = {
        "property_count": Property.objects.count(),
        "agent_count": Agent.objects.count(),
        "lead_count": Lead.objects.count(),
        "amenity_count": Amenity.objects.count(),
        "featured_properties": featured_properties,
        "wishlist_count": len(request.session.get("wishlist", [])),
        "compare_count": len(request.session.get("compare", [])),
    }
    return render(request, "core/home.html", context)


def _choices_list(choices):
    return [{"value": value, "label": label} for value, label in choices]


def _choices_map(choices):
    return {value: label for value, label in choices}


@role_required(UserProfile.Role.ADMIN)
def admin_console(request):
    property_types = _choices_list(Property.PropertyType.choices)
    listing_statuses = _choices_list(Property.ListingStatus.choices)
    pipeline_stages = _choices_list(Lead.PipelineStage.choices)
    amenity_types = _choices_list(Amenity.AmenityType.choices)
    agents = list(Agent.objects.order_by("name").values("id", "name"))

    admin_meta = {
        "propertyTypes": property_types,
        "listingStatuses": listing_statuses,
        "pipelineStages": pipeline_stages,
        "amenityTypes": amenity_types,
        "agents": agents,
        "maps": {
            "propertyType": _choices_map(Property.PropertyType.choices),
            "listingStatus": _choices_map(Property.ListingStatus.choices),
            "pipelineStage": _choices_map(Lead.PipelineStage.choices),
            "amenityType": _choices_map(Amenity.AmenityType.choices),
        },
        "entities": [
            {
                "key": "properties",
                "label": "Bất động sản",
                "description": "Quản lý tin đăng và chỉnh sửa đầy đủ metadata.",
                "columns": [
                    {"key": "id", "label": "ID"},
                    {"key": "title", "label": "Tiêu đề"},
                    {"key": "agent.name", "label": "Agent"},
                    {"key": "listing_status", "label": "Trạng thái", "map": "listingStatus"},
                    {"key": "property_type", "label": "Loại", "map": "propertyType"},
                    {"key": "price", "label": "Giá"},
                ],
                "fields": [
                    {"name": "title", "label": "Tiêu đề", "type": "text", "required": True},
                    {"name": "description", "label": "Mô tả", "type": "textarea"},
                    {"name": "property_type", "label": "Loại", "type": "select", "options": property_types},
                    {"name": "listing_status", "label": "Trạng thái", "type": "select", "options": listing_statuses},
                    {"name": "price", "label": "Giá (VNĐ)", "type": "number", "step": "0.01"},
                    {"name": "area", "label": "Diện tích (m²)", "type": "number", "step": "0.1"},
                    {"name": "address", "label": "Địa chỉ", "type": "text"},
                    {"name": "lat", "label": "Lat", "type": "number", "step": "0.000001"},
                    {"name": "lng", "label": "Lng", "type": "number", "step": "0.000001"},
                    {"name": "agent_id", "label": "Agent", "type": "select", "options": agents + [{"value": "", "label": "Không gắn"}]},
                    {"name": "is_featured", "label": "Đánh dấu featured", "type": "checkbox"},
                ],
                "endpoints": {
                    "collection": "/properties/admin-api/properties/",
                    "detail": "/properties/admin-api/properties/",
                },
            },
            {
                "key": "leads",
                "label": "Lead & Khách hàng",
                "description": "Theo dõi, tạo và cập nhật lead, bao gồm thông tin liên lạc và pipeline.",
                "columns": [
                    {"key": "id", "label": "ID"},
                    {"key": "name", "label": "Tên"},
                    {"key": "phone", "label": "Điện thoại"},
                    {"key": "pipeline_stage", "label": "Giai đoạn", "map": "pipelineStage"},
                    {"key": "assigned_agent.name", "label": "Agent"},
                    {"key": "budget", "label": "Ngân sách"},
                ],
                "fields": [
                    {"name": "name", "label": "Tên lead", "type": "text", "required": True},
                    {"name": "phone", "label": "Điện thoại", "type": "text", "required": True},
                    {"name": "budget", "label": "Ngân sách (VNĐ)", "type": "number", "step": "0.01"},
                    {"name": "property_interest", "label": "Quan tâm", "type": "text"},
                    {"name": "pipeline_stage", "label": "Giai đoạn", "type": "select", "options": pipeline_stages},
                    {"name": "assigned_agent_id", "label": "Agent", "type": "select", "options": agents + [{"value": "", "label": "Chưa gán"}]},
                    {"name": "lat", "label": "Lat", "type": "number", "step": "0.000001"},
                    {"name": "lng", "label": "Lng", "type": "number", "step": "0.000001"},
                    {"name": "notes", "label": "Ghi chú", "type": "textarea"},
                    {"name": "alert_enabled", "label": "Bật cảnh báo", "type": "checkbox"},
                ],
                "endpoints": {
                    "collection": "/admin-api/leads/",
                    "detail": "/admin-api/leads/",
                },
            },
            {
                "key": "agents",
                "label": "Môi giới",
                "description": "Quản lý tài khoản môi giới, vị trí và thông tin liên hệ.",
                "columns": [
                    {"key": "id", "label": "ID"},
                    {"key": "name", "label": "Tên"},
                    {"key": "email", "label": "Email"},
                    {"key": "phone", "label": "Điện thoại"},
                ],
                "fields": [
                    {"name": "name", "label": "Tên" , "type": "text", "required": True},
                    {"name": "email", "label": "Email", "type": "email", "required": True},
                    {"name": "phone", "label": "Điện thoại", "type": "text"},
                    {"name": "lat", "label": "Lat", "type": "number", "step": "0.000001"},
                    {"name": "lng", "label": "Lng", "type": "number", "step": "0.000001"},
                ],
                "endpoints": {
                    "collection": "/admin-api/agents/",
                    "detail": "/admin-api/agents/",
                },
            },
            {
                "key": "amenities",
                "label": "Tiện ích",
                "description": "Quản lý điểm tiện ích, loại và vị trí.",
                "columns": [
                    {"key": "id", "label": "ID"},
                    {"key": "name", "label": "Tên"},
                    {"key": "amenity_type", "label": "Loại", "map": "amenityType"},
                ],
                "fields": [
                    {"name": "name", "label": "Tên", "type": "text", "required": True},
                    {"name": "amenity_type", "label": "Loại", "type": "select", "options": amenity_types},
                    {"name": "lat", "label": "Lat", "type": "number", "step": "0.000001"},
                    {"name": "lng", "label": "Lng", "type": "number", "step": "0.000001"},
                ],
                "endpoints": {
                    "collection": "/admin-api/amenities/",
                    "detail": "/admin-api/amenities/",
                },
            },
        ],
    }
    return render(request, "core/admin_console.html", {"admin_meta": admin_meta})
