from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),  # login and logout
    path("dashboard/", include("dashboard.urls")),
    path("inventory/", include("inventory.urls")),
    path("", RedirectView.as_view(pattern_name="dashboard:home")),  # temporary, until the public site exists
]