from django.db import transaction
from django.shortcuts import redirect, render

from donations.forms import DonationForm
from donations.models import DonationPhoto, DonationSubmission, Donor


def _find_or_create_donor(data):
    """Reuse the same Donor if they have donated before (same phone or email)."""
    donor = None
    if data["phone"]:
        donor = Donor.objects.filter(phone=data["phone"].strip()).first()
    if donor is None and data["email"]:
        donor = Donor.objects.filter(email__iexact=data["email"]).first()
    if donor is None:
        donor = Donor.objects.create(
            name=data["name"],
            phone=data["phone"].strip(),
            email=data["email"],
            area=data["area"],
        )
    return donor


def donate(request):
    """Public donation form: no login needed (FR-12)."""
    if request.method == "POST":
        form = DonationForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            with transaction.atomic():  # donor, submission and photos are saved together
                donor = _find_or_create_donor(data)
                submission = DonationSubmission.objects.create(
                    donor=donor,
                    number_of_books=data["number_of_books"],
                    book_types=data["book_types"],
                    language=data["language"],
                    condition=data["condition"],
                    message=data["message"],
                    consent_given=True,
                )
                for photo in data["photos"]:
                    DonationPhoto.objects.create(submission=submission, image=photo)
            return redirect("public:donate_thanks")
    else:
        initial = {}
        if request.GET.get("n", "").isdigit():
            initial["number_of_books"] = int(request.GET["n"])
        if request.GET.get("lang") in {"rw", "en", "fr", "mixed", "other"}:
            initial["language"] = request.GET["lang"]
        form = DonationForm(initial=initial)
    return render(request, "public/donate.html", {"form": form})


def donate_thanks(request):
    return render(request, "public/donate_thanks.html")

# ---- Public home page: the showcase (FR-20) ----
from django.db.models import Sum

from communities.models import Recipient
from distribution.models import Distribution
from inventory.models import Book, InventoryLot

COVER_COLOURS = ["#FFE27A", "#FFD3B0", "#D9EFC4", "#CDE7F5", "#F6D1DD", "#FFF0A8"]


def showcase(request):
    """Books first, donating one click away. Only books staff approved are shown."""
    lots = InventoryLot.objects.exclude(status=InventoryLot.Status.REJECTED)
    still_here = lots.aggregate(n=Sum("quantity"))["n"] or 0
    given_out = Distribution.objects.aggregate(n=Sum("quantity"))["n"] or 0

    stats = {
        "books_collected": still_here + given_out,
        "donations": DonationSubmission.objects.exclude(
            status=DonationSubmission.Status.REJECTED).count(),
        "communities": Recipient.objects.filter(
            distributions__isnull=False).distinct().count(),
    }

    books = list(Book.objects.filter(show_in_showcase=True).order_by("-id")[:8])
    for i, book in enumerate(books):
        book.cover_colour = COVER_COLOURS[i % len(COVER_COLOURS)]

    return render(request, "public/showcase.html", {"stats": stats, "books": books})


# ---- Cover photos: public only for books approved for the homepage ----
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404


def book_cover(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if not book.cover_image:
        raise Http404
    if not (book.show_in_showcase or request.user.has_perm("inventory.view_book")):
        raise Http404
    return FileResponse(book.cover_image.open("rb"))
