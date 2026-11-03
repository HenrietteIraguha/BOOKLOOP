from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from communities.models import Recipient
from inventory.models import Book, InventoryLot

from .forms import RecordDistributionForm
from .models import Distribution

AVAILABLE = [InventoryLot.Status.ACCEPTED, InventoryLot.Status.IN_STORAGE]

BOOK_FILTERS = [
    ("language", "Language", "book__language", Book.Language.choices),
    ("education_level", "Level", "book__education_level", Book.EducationLevel.choices),
    ("book_type", "Type", "book__book_type", Book.BookType.choices),
]


@login_required
@permission_required("distribution.add_distribution", raise_exception=True)
def choose_books(request):
    """Pick a recipient and find available books that match their needs (FR-11)."""
    recipient = None
    recipient_id = request.GET.get("recipient", "")
    if recipient_id.isdigit():
        recipient = Recipient.objects.filter(pk=recipient_id).first()

    lots = InventoryLot.objects.select_related("book").filter(status__in=AVAILABLE, quantity__gt=0)

    query = request.GET.get("q", "").strip()
    if query:
        lots = lots.filter(
            Q(book__title__icontains=query) | Q(book__author__icontains=query) | Q(book__subject__icontains=query)
        )

    filters = []
    for name, label, field, choices in BOOK_FILTERS:
        selected = request.GET.get(name, "")
        if selected:
            lots = lots.filter(**{field: selected})
        filters.append({"name": name, "label": label, "choices": choices, "selected": selected})

    return render(request, "distribution/choose_books.html", {
        "recipients": Recipient.objects.all(),
        "recipient": recipient,
        "lots": lots.order_by("book__title"),
        "query": query,
        "filters": filters,
    })


@login_required
@permission_required("distribution.add_distribution", raise_exception=True)
def confirm_distribution(request, lot_pk, recipient_pk):
    """Confirmation step (NFR-16), then record, reduce the inventory and update the status together (FR-17)."""
    lot = get_object_or_404(InventoryLot.objects.select_related("book"), pk=lot_pk)
    recipient = get_object_or_404(Recipient, pk=recipient_pk)
    form = RecordDistributionForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        quantity = form.cleaned_data["quantity"]
        with transaction.atomic():
            # Lock the lot so two operators can't give away the same copies (SRS 2.5 #5).
            locked = InventoryLot.objects.select_for_update().get(pk=lot.pk)
            if locked.status not in AVAILABLE or locked.quantity < quantity:
                form.add_error("quantity", f"Only {locked.quantity} copies are available now.")
            else:
                Distribution.objects.create(
                    lot=locked,
                    recipient=recipient,
                    quantity=quantity,
                    distribution_date=form.cleaned_data["distribution_date"],
                    notes=form.cleaned_data["notes"],
                    recorded_by=request.user,
                )
                locked.quantity -= quantity
                if locked.quantity == 0:
                    locked.status = InventoryLot.Status.DISTRIBUTED  # logged in the status history
                locked._changed_by = request.user
                locked.save()

                messages.success(
                    request,
                    f'Recorded {quantity} cop{"y" if quantity == 1 else "ies"} of "{lot.book.title}" '
                    f"given to {recipient.name}. {locked.quantity} left in this lot.",
                )
                return redirect(f"{reverse('distribution:choose')}?recipient={recipient.pk}")

    return render(request, "distribution/confirm.html", {"lot": lot, "recipient": recipient, "form": form})


@login_required
@permission_required("distribution.view_distribution", raise_exception=True)
def distribution_list(request):
    """Everything given out, newest first."""
    distributions = Distribution.objects.select_related("lot__book", "recipient", "recorded_by")
    recipient_id = request.GET.get("recipient", "")
    if recipient_id.isdigit():
        distributions = distributions.filter(recipient_id=recipient_id)
    total = distributions.aggregate(total=Sum("quantity"))["total"] or 0
    return render(request, "distribution/distribution_list.html", {
        "distributions": distributions,
        "recipients": Recipient.objects.all(),
        "selected_recipient": recipient_id,
        "total": total,
    })
