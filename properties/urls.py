from django.urls import path

from . import views

urlpatterns = [
    path("", views.property_list, name="list"),
    path("<int:pk>/", views.property_detail, name="detail"),
    path("nearby/search/", views.nearby_search, name="nearby_search"),
    path("amenities/search/", views.amenity_search, name="amenity_search"),
]
