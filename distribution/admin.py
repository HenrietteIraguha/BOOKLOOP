from django.contrib import admin

from .models import Distribution


@admin.register(Distribution)
class DistributionAdmin(admin.ModelAdmin):
    """View-only: distributions are recorded through the dashboard, which updates the inventory."""

    list_display = ["distribution_date", "lot", "recipient", "quantity", "recorded_by"]
    list_filter = ["distribution_date", "recipient"]
    search_fields = ["lot__book__title", "recipient__name"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
