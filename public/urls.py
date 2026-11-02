from django.urls import path

from . import views

app_name = "public"

urlpatterns = [
    path("donate/", views.donate, name="donate"),
    path("donate/thanks/", views.donate_thanks, name="donate_thanks"),
]
