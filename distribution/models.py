from datetime import date

from django.conf import settings
from django.db import models


class Distribution(models.Model):
    """Copies from one lot given to one recipient on one date (FR-17)."""

    lot = models.ForeignKey("inventory.InventoryLot", on_delete=models.PROTECT, related_name="distributions")
    recipient = models.ForeignKey("communities.Recipient", on_delete=models.PROTECT, related_name="distributions")
    quantity = models.PositiveIntegerField()
    distribution_date = models.DateField(default=date.today)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="distributions_recorded",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-distribution_date", "-created_at"]

    def __str__(self):
        return f"{self.quantity} x {self.lot.book.title} to {self.recipient} ({self.distribution_date:%d %b %Y})"
