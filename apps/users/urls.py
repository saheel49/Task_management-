from django.urls import path

from . import views

app_name = "users"
urlpatterns = [
    path("profile/", views.profile, name="user_profile"),
    path("profile/upload-image/", views.upload_profile_image, name="upload_profile_image"),
    path("list/", views.user_list, name="user_list"),
    path("<int:pk>/", views.user_detail, name="user_detail"),
]
