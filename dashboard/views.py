from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render

from inventory.models import Book, InventoryLot


@login_required  
def home(request):
    available = InventoryLot.objects.filter(
        status__in=[InventoryLot.Status.ACCEPTED, InventoryLot.Status.IN_STORAGE]
    ).aggregate(total=Sum("quantity"))["total"] or 0

    context = {
        "book_count": Book.objects.count(),
        "lot_count": InventoryLot.objects.count(),
        "available_copies": available,
    }
    return render(request, "dashboard/home.html", context)