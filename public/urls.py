from django.urls import path

from . import views

app_name = "public"

urlpatterns = [
    path("covers/<int:pk>/", views.book_cover, name="cover"),
    path("", views.showcase, name="home"),
    path("donate/", views.donate, name="donate"),
    path("donate/thanks/", views.donate_thanks, name="donate_thanks"),
]
