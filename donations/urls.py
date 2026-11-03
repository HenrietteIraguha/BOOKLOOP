from django.urls import path

from . import views

app_name = "donations"

urlpatterns = [
    path("", views.donation_list, name="list"),
    path("<int:pk>/", views.donation_detail, name="detail"),
    path("photos/<int:pk>/", views.donation_photo, name="photo"),
]
