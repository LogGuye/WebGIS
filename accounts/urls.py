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
    path('password-reset/', views.password_reset_view, name='password_reset'),
    path('password-reset/done/', views.password_reset_done_view, name='password_reset_done'),
    path('password-reset/confirm/', views.password_reset_confirm_view, name='password_reset_confirm'),
]

