from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render

from donations.models import DonationSubmission
from inventory.models import Book, InventoryLot


@login_required  # FR-15: only logged-in users can see the dashboard
def home(request):
    available = InventoryLot.objects.filter(
        status__in=[InventoryLot.Status.ACCEPTED, InventoryLot.Status.IN_STORAGE]
    ).aggregate(total=Sum("quantity"))["total"] or 0

    context = {
        "book_count": Book.objects.count(),
        "lot_count": InventoryLot.objects.count(),
        "available_copies": available,
        "pending_donations": DonationSubmission.objects.filter(
            status=DonationSubmission.Status.PENDING
        ).count(),
    }
    return render(request, "dashboard/home.html", context)
