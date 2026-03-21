import csv
from io import TextIOWrapper

from django.contrib import admin, messages
from django.contrib.gis.geos import Point
from django.utils import timezone

from .models import Amenity, Property, PropertyChangeLog, PropertyImage


def mark_active(modeladmin, request, queryset):
    updated = queryset.update(listing_status=Property.ListingStatus.ACTIVE)
    messages.success(request, f"Updated {updated} properties to active.")
mark_active.short_description = "Mark selected properties as active"


def mark_sold(modeladmin, request, queryset):
    updated = queryset.update(listing_status=Property.ListingStatus.SOLD)
    messages.success(request, f"Updated {updated} properties to sold.")
mark_sold.short_description = "Mark selected properties as sold"


def mark_hidden(modeladmin, request, queryset):
    updated = queryset.update(listing_status=Property.ListingStatus.HIDDEN)
    messages.success(request, f"Updated {updated} properties to hidden.")
mark_hidden.short_description = "Hide selected properties"


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1
    fields = ("image", "caption", "is_primary", "sort_order")


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("title", "property_type", "listing_status", "is_featured", "price", "area", "agent", "updated_at")
    search_fields = ("title", "address", "description")
    list_filter = ("property_type", "listing_status", "is_featured", "agent")
    list_editable = ("listing_status", "is_featured")
    filter_horizontal = ("amenities",)
    inlines = [PropertyImageInline]
    actions = (mark_active, mark_sold, mark_hidden)

    fieldsets = (
        (None, {"fields": ("title", "description", "property_type", "listing_status", "is_featured")}),
        ("Pricing & size", {"fields": ("price", "area")}),
        ("Location", {"fields": ("address", "location")}),
        ("Relations", {"fields": ("agent", "amenities")}),
    )

    def save_model(self, request, obj, form, change):
        action = "updated" if change else "created"
        super().save_model(request, obj, form, change)
        PropertyChangeLog.objects.create(
            property=obj,
            action=action,
            summary=f"Property {action} via admin at {timezone.now():%Y-%m-%d %H:%M}",
        )


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ("name", "amenity_type")
    list_filter = ("amenity_type",)
    search_fields = ("name",)


@admin.register(PropertyChangeLog)
class PropertyChangeLogAdmin(admin.ModelAdmin):
    list_display = ("property", "action", "summary", "created_at")
    list_filter = ("action", "created_at")
    search_fields = ("property__title", "summary")
    readonly_fields = ("property", "action", "summary", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


class PropertyCsvImportAdmin(admin.ModelAdmin):
    change_list_template = "admin/properties/property/change_list.html"

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom = [
            path("import-csv/", self.admin_site.admin_view(self.import_csv_view), name="properties_property_import_csv"),
        ]
        return custom + urls

    def import_csv_view(self, request):
        from django.shortcuts import redirect, render

        if request.method == "POST" and request.FILES.get("csv_file"):
            file = TextIOWrapper(request.FILES["csv_file"].file, encoding="utf-8")
            reader = csv.DictReader(file)
            created = 0
            for row in reader:
                lat = float(row["lat"])
                lng = float(row["lng"])
                Property.objects.create(
                    title=row["title"],
                    description=row.get("description", ""),
                    property_type=row["property_type"],
                    listing_status=row.get("listing_status", Property.ListingStatus.ACTIVE),
                    is_featured=str(row.get("is_featured", "")).lower() in {"1", "true", "yes"},
                    price=row["price"],
                    area=row["area"],
                    address=row["address"],
                    location=Point(lng, lat, srid=4326),
                )
                created += 1
            self.message_user(request, f"Đã nhập {created} bất động sản từ tệp CSV.", level=messages.SUCCESS)
            return redirect("..")

        return render(request, "admin/properties/property/import_csv.html", {})


admin.site.unregister(Property)
admin.site.register(Property, type("PropertyAdminWithImport", (PropertyCsvImportAdmin, PropertyAdmin), {}))
, {}))
roperty, type("PropertyAdminWithImport", (PropertyCsvImportAdmin, PropertyAdmin), {}))
