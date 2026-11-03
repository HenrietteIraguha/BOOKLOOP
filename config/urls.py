from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),  # login and logout
    path("dashboard/", include("dashboard.urls")),
    path("inventory/", include("inventory.urls")),
    path("donations/", include("donations.urls")),
    path("recipients/", include("communities.urls")),
    path("distribution/", include("distribution.urls")),
    path("", include("public.urls")),
    path("", RedirectView.as_view(pattern_name="public:donate")),  # until the showcase home page exists
]
