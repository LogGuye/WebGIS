from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

from .models import UserProfile


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
                messages.error(request, "Bạn không có quyền truy cập trang này.")
                return redirect("core:home")
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator


def role_context(request):
    role = _role(request.user)
    return {
        "current_role": role,
        "is_admin_role": role == UserProfile.Role.ADMIN,
        "is_agent_role": role == UserProfile.Role.AGENT,
        "is_user_role": role == UserProfile.Role.USER,
    }
