from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import redirect

from leads.models import Lead
from properties.models import Amenity, Property

from .models import Agent, UserProfile


def _role(user):
    if not user.is_authenticated:
        return None
    if user.is_superuser or user.is_staff:
        return UserProfile.Role.ADMIN
    return getattr(getattr(user, "profile", None), "role", UserProfile.Role.USER)


def role_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f"/accounts/login/?next={request.path}")
            
            if _role(request.user) not in allowed_roles:
                raise PermissionDenied
                
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator


def role_context(request):
    role = _role(getattr(request, "user", None)) if hasattr(request, "user") else None
    session = getattr(request, "session", {}) or {}
    return {
        "current_role": role,
        "is_admin_role": role == UserProfile.Role.ADMIN,
        "is_agent_role": role == UserProfile.Role.AGENT,
        "is_user_role": role == UserProfile.Role.USER,
        "property_count": Property.objects.count(),
        "agent_count": Agent.objects.count(),
        "lead_count": Lead.objects.count(),
        "amenity_count": Amenity.objects.count(),
        "wishlist_count": len(session.get("wishlist", [])),
        "compare_count": len(session.get("compare", [])),
    }
