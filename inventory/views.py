from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.shortcuts import redirect, render
from django.core.paginator import Paginator
from django.db.models import Q, Sum

from .forms import BookForm, LotForm
from .isbn import lookup_isbn, normalise_isbn
from .models import Book, InventoryLot

SUGGESTED_FIELDS = ["title", "author", "publisher"]


def _values_from_post(post, prefix, fields):
    """Keep what the operator already typed when the page reloads."""
    return {field: post.get(f"{prefix}-{field}", "") for field in fields}


@login_required
@permission_required("inventory.add_book", raise_exception=True)
def register_book(request):
    suggestion = {}

    
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


    elif request.method == "POST":
        book_form = BookForm(request.POST, prefix="book")
        lot_form = LotForm(request.POST, prefix="lot")
        suggestion = {f: request.POST.get(f"suggested_{f}", "").strip() for f in SUGGESTED_FIELDS}
        if not any(suggestion.values()):
            suggestion = {}

        if book_form.is_valid() and lot_form.is_valid():

            source = Book.ClassificationSource.MANUAL
            if suggestion:
                unchanged = all(book_form.cleaned_data[f] == suggestion[f] for f in SUGGESTED_FIELDS)
                source = (Book.ClassificationSource.TOOL_CONFIRMED if unchanged
                          else Book.ClassificationSource.TOOL_CORRECTED)

            with transaction.atomic(): 

                isbn = book_form.cleaned_data["isbn"]
                book = Book.objects.filter(isbn=isbn).first() if isbn else None
                existing = book is not None
                if not existing:
                    book = book_form.save(commit=False)
                    book.classification_source = source
                    book.save()

                lot = lot_form.save(commit=False)
                lot.book = book
                lot._changed_by = request.user  
                lot.save()

            if existing:
                text = f'Added {lot.quantity} copies to the existing book "{book.title}".'
            else:
                text = f'Saved "{book.title}" with {lot.quantity} copies.'
            messages.success(request, text + " You can register the next book.")
            return redirect("inventory:register_book")  # the "More books?" loop

    else:
        book_form = BookForm(prefix="book")
        lot_form = LotForm(prefix="lot")

    return render(request, "inventory/register_book.html", {
        "book_form": book_form,
        "lot_form": lot_form,
        "suggestion": suggestion,
    })



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