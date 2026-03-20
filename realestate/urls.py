from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("", include(("core.urls", "core"), namespace="core")),
    path("properties/", include(("properties.urls", "properties"), namespace="properties")),
    path("leads/", include(("leads.urls", "leads"), namespace="leads")),
]
