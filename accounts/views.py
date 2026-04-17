from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
import random
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import PasswordResetCode, User

from leads.models import Lead
from properties.models import Property

from .forms import LoginForm, ProfileForm, RegisterForm
from .models import Agent, UserProfile


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


def agent_public_profile(request, pk):
    agent = get_object_or_404(Agent, pk=pk)
    properties = Property.objects.filter(agent=agent, listing_status=Property.ListingStatus.ACTIVE).prefetch_related("images")[:6]
    lead_count = Lead.objects.filter(assigned_agent=agent).count()
    active_count = Property.objects.filter(agent=agent, listing_status=Property.ListingStatus.ACTIVE).count()
    sold_count = Property.objects.filter(agent=agent, listing_status=Property.ListingStatus.SOLD).count()
    return render(request, "accounts/agent_public_profile.html", {
        "agent": agent,
        "properties": properties,
        "lead_count": lead_count,
        "active_count": active_count,
        "sold_count": sold_count,
    })


def send_reset_code(request):
    if request.method == "POST":
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()
        if user:
            # Tạo mã 6 số ngẫu nhiên
            code = f"{random.randint(100000, 999999)}"
            PasswordResetCode.objects.create(user=user, code=code)
            
            # Gửi qua Mailtrap
            send_mail(
                'Mã xác nhận đổi mật khẩu',
                f'Mã xác nhận của bạn là: {code}. Mã có hiệu lực trong 10 phút.',
                'noreply@geoestate.vn',
                [email],
            )
            request.session['reset_email'] = email # Lưu email vào session để dùng bước sau
            return redirect('accounts:verify_code')
    return render(request, 'accounts/password_reset_form.html')

def verify_code(request):
    email = request.session.get('reset_email')
    if request.method == "POST":
        code = request.POST.get('code')
        new_password = request.POST.get('password')
        
        reset_entry = PasswordResetCode.objects.filter(user__email=email, code=code).last()
        
        if reset_entry and reset_entry.is_valid():
            user = reset_entry.user
            user.set_password(new_password)
            user.save()
            reset_entry.is_used = True
            reset_entry.save()
            messages.success(request, "Đổi mật khẩu thành công!")
            return redirect('accounts:login')
        else:
            messages.error(request, "Mã xác nhận không đúng hoặc đã hết hạn.")
            
    return render(request, 'accounts/password_verify_code.html')


def password_reset_view(request):
    if request.method == "POST":
        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()
        if user:
            # 1. Tạo mã OTP 6 số
            code = f"{random.randint(100000, 999999)}"
            PasswordResetCode.objects.create(user=user, code=code)
            
            # 2. Gửi mail qua Mailtrap
            context = {'reset_code': code, 'user': user}
            html_message = render_to_string('accounts/password_reset_email.html', context)
            send_mail(
                'Mã xác nhận khôi phục mật khẩu - GeoEstate',
                f'Mã của bạn là: {code}',
                'noreply@geoestate.vn',
                [email],
                html_message=html_message
            )
            
            # 3. Lưu email vào session và chuyển sang trang nhập code
            request.session['reset_email'] = email
            return redirect('accounts:password_reset_done')
        else:
            messages.error(request, "Email này không tồn tại trong hệ thống.")
    return render(request, 'accounts/password_reset.html')

def password_reset_done_view(request):
    email = request.session.get('reset_email')
    if not email:
        return redirect('accounts:password_reset')

    if request.method == "POST":
        code = request.POST.get('code')
        # Kiểm tra mã OTP trong database
        reset_entry = PasswordResetCode.objects.filter(user__email=email, code=code).last()
        
        if reset_entry and reset_entry.is_valid():
            # Xác thực thành công, cho phép qua trang đổi mật khẩu
            request.session['otp_verified'] = True
            return redirect('accounts:password_reset_confirm')
        else:
            messages.error(request, "Mã xác nhận không đúng hoặc đã hết hạn.")
            
    return render(request, 'accounts/password_reset_done.html', {'email': email})

def password_reset_confirm_view(request):
    # Bảo vệ: Nếu chưa qua bước nhập code thì không cho vào trang này
    if not request.session.get('otp_verified'):
        return redirect('accounts:password_reset')

    if request.method == "POST":
        password = request.POST.get('password')
        email = request.session.get('reset_email')
        
        user = User.objects.get(email=email)
        user.set_password(password)
        user.save()
        
        # Xóa session sau khi hoàn tất
        del request.session['reset_email']
        del request.session['otp_verified']
        
        messages.success(request, "Mật khẩu đã được cập nhật. Hãy đăng nhập lại.")
        return redirect('accounts:login')
        
    return render(request, 'accounts/password_reset_confirm.html')