from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q, Sum
from django.shortcuts import redirect, render
from django.urls import reverse

from donations.models import DonationSubmission

from .forms import BookForm, LotForm
from .isbn import lookup_isbn, normalise_isbn
from .models import Book, InventoryLot

# Fields that the ISBN lookup can suggest (FR-02)
SUGGESTED_FIELDS = ["title", "author", "publisher"]


def _values_from_post(post, prefix, fields):
    """Keep what the operator already typed when the page reloads."""
    return {field: post.get(f"{prefix}-{field}", "") for field in fields}


def _get_donation(request):
    """The donation these books came from, if any (FR-14)."""
    donation_id = request.GET.get("donation") or request.POST.get("donation_id")
    if donation_id and str(donation_id).isdigit():
        return DonationSubmission.objects.select_related("donor").filter(pk=donation_id).first()
    return None


@login_required
@permission_required("inventory.add_book", raise_exception=True)
def register_book(request):
    suggestion = {}
    donation = _get_donation(request)

    # 1. "Look up" button: fill in details from the ISBN (FR-02, FR-04)
    if request.method == "POST" and request.POST.get("action") == "lookup":
        book_values = _values_from_post(request.POST, "book", BookForm.Meta.fields)
        lot_values = _values_from_post(request.POST, "lot", LotForm.Meta.fields)
        raw_isbn = book_values["isbn"].strip()

        if not raw_isbn:
            messages.warning(request, "Type or scan an ISBN first.")
        elif normalise_isbn(raw_isbn) is None:
            messages.warning(request, "That is not a valid ISBN. Check the number, or enter the details manually.")
        else:
            result = lookup_isbn(raw_isbn)
            book_values["isbn"] = normalise_isbn(raw_isbn)
            if result:
                for field in SUGGESTED_FIELDS:
                    book_values[field] = result[field]
                suggestion = {field: result[field] for field in SUGGESTED_FIELDS}
                messages.info(request, f"Details found in {result['source']}. Please check them and complete the rest.")
            else:
                messages.warning(request, "This book was not found online. Please enter its details manually.")

        book_form = BookForm(initial=book_values, prefix="book")
        lot_form = LotForm(initial=lot_values, prefix="lot")

    # 2. "Save book" button: save the book, its lot and the first log entry
    elif request.method == "POST":
        book_form = BookForm(request.POST, prefix="book")
        lot_form = LotForm(request.POST, prefix="lot")
        suggestion = {f: request.POST.get(f"suggested_{f}", "").strip() for f in SUGGESTED_FIELDS}
        if not any(suggestion.values()):
            suggestion = {}

        if book_form.is_valid() and lot_form.is_valid():
            # How were the details obtained? (NFR-12)
            source = Book.ClassificationSource.MANUAL
            if suggestion:
                unchanged = all(book_form.cleaned_data[f] == suggestion[f] for f in SUGGESTED_FIELDS)
                source = (Book.ClassificationSource.TOOL_CONFIRMED if unchanged
                          else Book.ClassificationSource.TOOL_CORRECTED)

            with transaction.atomic():  # save everything, or nothing
                isbn = book_form.cleaned_data["isbn"]
                book = Book.objects.filter(isbn=isbn).first() if isbn else None
                existing = book is not None
                if not existing:
                    book = book_form.save(commit=False)
                    book.classification_source = source
                    book.save()

                lot = lot_form.save(commit=False)
                lot.book = book
                lot.donation = donation  # FR-14: trace the copies back to their donation
                lot._changed_by = request.user  # recorded in the status history
                lot.save()

                # Books are registered after collection, so mark the donation as collected.
                if donation and donation.status in (DonationSubmission.Status.PENDING,
                                                    DonationSubmission.Status.CONTACTED):
                    donation.status = DonationSubmission.Status.COLLECTED
                    donation.save(update_fields=["status", "updated_at"])

            if existing:
                text = f'Added {lot.quantity} copies to the existing book "{book.title}".'
            else:
                text = f'Saved "{book.title}" with {lot.quantity} copies.'
            messages.success(request, text + " You can register the next book.")

            url = reverse("inventory:register_book")
            if donation:
                url += f"?donation={donation.pk}"
            return redirect(url)  # the "More books?" loop

    # 3. Opening the page: empty forms
    else:
        book_form = BookForm(prefix="book")
        lot_form = LotForm(prefix="lot")

    return render(request, "inventory/register_book.html", {
        "book_form": book_form,
        "lot_form": lot_form,
        "suggestion": suggestion,
        "donation": donation,
    })


# Filters on the inventory page: (name in the address bar, label, model field, choices)
INVENTORY_FILTERS = [
    ("language", "Language", "book__language", Book.Language.choices),
    ("book_type", "Type", "book__book_type", Book.BookType.choices),
    ("education_level", "Level", "book__education_level", Book.EducationLevel.choices),
    ("condition", "Condition", "condition", InventoryLot.Condition.choices),
    ("status", "Status", "status", InventoryLot.Status.choices),
]


@login_required
@permission_required("inventory.view_inventorylot", raise_exception=True)
def inventory_list(request):
    """Search and filter the inventory (FR-18)."""
    lots = InventoryLot.objects.select_related("book")

    query = request.GET.get("q", "").strip()
    if query:
        lots = lots.filter(
            Q(book__title__icontains=query)
            | Q(book__author__icontains=query)
            | Q(book__isbn__icontains=query)
            | Q(book__subject__icontains=query)
        )

    filters = []
    for name, label, field, choices in INVENTORY_FILTERS:
        selected = request.GET.get(name, "")
        if selected:
            lots = lots.filter(**{field: selected})
        filters.append({"name": name, "label": label, "choices": choices, "selected": selected})

    lots = lots.order_by("book__title", "-date_collected")
    total_copies = lots.aggregate(total=Sum("quantity"))["total"] or 0
    page = Paginator(lots, 25).get_page(request.GET.get("page"))

    # Keep the search and filters when moving between pages
    params = request.GET.copy()
    params.pop("page", None)

    return render(request, "inventory/inventory_list.html", {
        "page": page,
        "query": query,
        "filters": filters,
        "total_lots": page.paginator.count,
        "total_copies": total_copies,
        "querystring": params.urlencode(),
    })


# ---- Homepage showcase management (FR-20) ----
import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from donations.images import check_and_clean_image
from .models import Book


@login_required
@permission_required("inventory.change_book", raise_exception=True)
def showcase_manage(request):
    """Operators choose which books appear on the public homepage and add covers."""
    if request.method == "POST":
        book = get_object_or_404(Book, pk=request.POST.get("book_id"))
        action = request.POST.get("action")

        if action == "show":
            book.show_in_showcase = True
            book.save()
            messages.success(request, f"“{book.title}” is now on the homepage.")
        elif action == "hide":
            book.show_in_showcase = False
            book.save()
            messages.success(request, f"“{book.title}” was removed from the homepage.")
        elif action == "upload":
            upload = request.FILES.get("cover")
            if not upload:
                messages.error(request, "Choose a photo first.")
            else:
                try:
                    cleaned = check_and_clean_image(upload)  # size, type, resize, strip location data
                except ValidationError as error:
                    messages.error(request, " ".join(error.messages))
                else:
                    ext = os.path.splitext(getattr(cleaned, "name", "") or upload.name)[1].lower() or ".jpg"
                    if book.cover_image:
                        book.cover_image.delete(save=False)
                    book.cover_image.save(f"book-{book.pk}{ext}", cleaned, save=True)
                    messages.success(request, f"Cover added to “{book.title}”.")
        elif action == "remove_cover" and book.cover_image:
            book.cover_image.delete(save=True)
            messages.success(request, f"Cover removed from “{book.title}”.")

        return redirect(request.get_full_path())

    query = request.GET.get("q", "").strip()
    books = Book.objects.order_by("-show_in_showcase", "title")
    if query:
        books = books.filter(Q(title__icontains=query) | Q(author__icontains=query) | Q(isbn__icontains=query))
    page = Paginator(books, 20).get_page(request.GET.get("page"))
    shown = Book.objects.filter(show_in_showcase=True).count()
    return render(request, "inventory/showcase_manage.html",
                  {"page": page, "query": query, "shown": shown})


# ---- Change a lot's status (FR9) ----
from django.views.decorators.http import require_POST

from .models import InventoryLot

MANUAL_STATUSES = [
    InventoryLot.Status.PENDING_ASSESSMENT,
    InventoryLot.Status.ACCEPTED,
    InventoryLot.Status.REJECTED,
    InventoryLot.Status.IN_STORAGE,
    InventoryLot.Status.ALLOCATED,
]


@login_required
@permission_required("inventory.change_inventorylot", raise_exception=True)
@require_POST
def change_lot_status(request, pk):
    """Move a lot through assessment, storage and allocation.
    'Distributed' is only set by recording a distribution (FR17)."""
    lot = get_object_or_404(InventoryLot, pk=pk)
    new_status = request.POST.get("status", "")

    if lot.status == InventoryLot.Status.DISTRIBUTED:
        messages.error(request, f"“{lot.book.title}” has already been distributed, so its status cannot change.")
    elif new_status not in MANUAL_STATUSES:
        messages.error(request, "Choose a valid status.")
    elif new_status == lot.status:
        messages.info(request, f"“{lot.book.title}” already has that status.")

    else:
        old_label = lot.get_status_display()
        lot.status = new_status
        lot._changed_by = request.user  # recorded in the status history
        lot.save()
        messages.success(request, f"“{lot.book.title}”: {old_label} → {lot.get_status_display()}.")

    next_url = request.POST.get("next", "")
    return redirect(next_url if next_url.startswith("/inventory/") else "inventory:list")
