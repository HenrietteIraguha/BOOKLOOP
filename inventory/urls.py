from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    path("showcase/", views.showcase_manage, name="showcase"),
    path("register/", views.register_book, name="register_book"),
    path("", views.inventory_list, name="list"),
]