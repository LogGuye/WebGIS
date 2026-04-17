from django.urls import path
from django.urls import reverse_lazy
from . import views
from django.contrib.auth import views as auth_view

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("agents/<int:pk>/", views.agent_public_profile, name="agent_public_profile"),
    
    path('password-reset/', 
         auth_view.PasswordResetView.as_view(
             template_name='accounts/password_reset.html',
             email_template_name='accounts/password_reset_email.html', # Chỉ định file mail vừa tạo
             success_url=reverse_lazy('accounts:password_reset_done')
         ), 
         name='password_reset'),
    path('password-reset/done/', 
         auth_view.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'), 
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', 
         auth_view.PasswordResetConfirmView.as_view(
             template_name='accounts/password_reset_confirm.html',
             success_url=reverse_lazy('accounts:password_reset_complete') # Quan trọng
         ), 
         name='password_reset_confirm'),
    path('password-reset-complete/', 
         auth_view.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'), 
         name='password_reset_complete'),
]
