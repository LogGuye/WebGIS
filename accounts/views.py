from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import LoginForm, ProfileForm, RegisterForm
from .models import UserProfile


def _role_home(user):
    profile = getattr(user, "profile", None)
    role = getattr(profile, "role", UserProfile.Role.USER)
    if role in (UserProfile.Role.AGENT, UserProfile.Role.ADMIN):
        return "leads:dashboard_home"
    return "leads:customer_dashboard"


def register_view(request):
    if request.user.is_authenticated:
        return redirect(_role_home(request.user))

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Tạo tài khoản thành công.")
        return redirect(_role_home(user))
    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect(_role_home(request.user))

    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, "Đăng nhập thành công.")
        next_url = request.GET.get("next") or request.POST.get("next")
        return redirect(next_url or _role_home(user))
    return render(request, "accounts/login.html", {"form": form, "next": request.GET.get("next", "")})


def logout_view(request):
    logout(request)
    messages.success(request, "Đã đăng xuất.")
    return redirect("core:home")


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    form = ProfileForm(request.POST or None, instance=profile, user=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Đã cập nhật hồ sơ.")
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html", {"form": form, "profile": profile})
