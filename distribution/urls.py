from django.urls import path

from . import views

app_name = "distribution"

urlpatterns = [
    path("", views.distribution_list, name="list"),
    path("record/", views.choose_books, name="choose"),
    path("record/<int:lot_pk>/<int:recipient_pk>/", views.confirm_distribution, name="confirm"),
]
