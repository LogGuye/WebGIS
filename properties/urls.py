from django.urls import path

from . import views

urlpatterns = [
    path("", views.property_list, name="list"),
    path("<int:pk>/", views.property_detail, name="detail"),
    path("nearby/search/", views.nearby_search, name="nearby_search"),
    path("amenities/search/", views.amenity_search, name="amenity_search"),
    path("api/geojson/", views.property_geojson, name="property_geojson"),
    path("<int:pk>/amenity-stats/", views.property_amenity_stats, name="property_amenity_stats"),
    path("<int:pk>/similar/", views.similar_properties_api, name="similar_properties_api"),
    path("api/map-bounds/", views.map_bounds_search_api, name="map_bounds_search"),
    path("<int:pk>/nearest-amenities/", views.property_nearest_amenities, name="nearest_amenities"),
]
