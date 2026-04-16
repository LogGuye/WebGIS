from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.shortcuts import render

from core import views as core_views
def custom_404(request, exception):
    return render(request, '404.html', status=404)

def custom_403(request, exception=None):
    return render(request, '403.html', status=403)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("console/", core_views.admin_console, name="admin_console"),
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("", include(("core.urls", "core"), namespace="core")),
    path("properties/", include(("properties.urls", "properties"), namespace="properties")),
    path("leads/", include(("leads.urls", "leads"), namespace="leads")),
]

handler404 = custom_404
handler403 = custom_403

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [
        path('test404/', custom_404, {'exception': Exception()}),
        path('test403/', custom_403),
    ]