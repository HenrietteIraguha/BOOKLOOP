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
        form = DonationForm()
    return render(request, "public/donate.html", {"form": form})


def donate_thanks(request):
    return render(request, "public/donate_thanks.html")