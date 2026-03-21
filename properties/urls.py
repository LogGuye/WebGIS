from django.urls import path

from . import views

urlpatterns = [
    path("", views.property_list, name="list"),
    path("create/", views.property_create, name="create"),
    path("<int:pk>/images/", views.property_images_manage, name="images_manage"),
    path("<int:pk>/images/upload/", views.property_images_upload, name="images_upload"),
    path("images/<int:image_id>/primary/", views.property_image_set_primary, name="image_set_primary"),
    path("images/<int:image_id>/delete/", views.property_image_delete, name="image_delete"),
    path("images/<int:image_id>/reorder/", views.property_image_reorder, name="image_reorder"),
    path("saved-searches/create/", views.saved_search_create, name="saved_search_create"),
    path("saved-searches/<int:pk>/delete/", views.saved_search_delete, name="saved_search_delete"),
    path("map/data/", views.property_map_data, name="map_data"),
    path("wishlist/", views.wishlist_view, name="wishlist"),
    path("compare/", views.compare_view, name="compare"),
    path("<int:pk>/wishlist-toggle/", views.wishlist_toggle, name="wishlist_toggle"),
    path("<int:pk>/compare-toggle/", views.compare_toggle, name="compare_toggle"),
    path("<int:pk>/", views.property_detail, name="detail"),
    path("nearby/search/", views.nearby_search, name="nearby_search"),
    path("amenities/search/", views.amenity_search, name="amenity_search"),
]
