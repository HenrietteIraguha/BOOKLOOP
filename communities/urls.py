from django.urls import path

from . import views

app_name = "communities"

urlpatterns = [
    path("", views.recipient_list, name="list"),
    path("add/", views.recipient_create, name="add"),
    path("<int:pk>/edit/", views.recipient_edit, name="edit"),
]
