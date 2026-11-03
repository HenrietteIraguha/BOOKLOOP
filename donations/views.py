from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Count
from django.http import FileResponse
from django.shortcuts import get_object_or_404, redirect, render

from .models import DonationPhoto, DonationSubmission


class StatusForm(forms.Form):
    status = forms.ChoiceField(choices=DonationSubmission.Status.choices, label="Donation status")


@login_required
@permission_required("donations.view_donationsubmission", raise_exception=True)
def donation_list(request):
    """All donation submissions, filterable by status (FR-13)."""
    selected = request.GET.get("status", "")
    submissions = DonationSubmission.objects.select_related("donor").annotate(photo_count=Count("photos"))
    if selected:
        submissions = submissions.filter(status=selected)

    counts = dict(
        DonationSubmission.objects.order_by().values_list("status").annotate(n=Count("id"))
    )
    tabs = [
        {"value": value, "label": label, "count": counts.get(value, 0)}
        for value, label in DonationSubmission.Status.choices
    ]
    return render(request, "donations/donation_list.html", {
        "submissions": submissions,
        "tabs": tabs,
        "selected": selected,
        "total": sum(counts.values()),
    })


@login_required
@permission_required("donations.view_donationsubmission", raise_exception=True)
def donation_detail(request, pk):
    """One submission: details, photos, status update and linked books (FR-13, FR-14)."""
    submission = get_object_or_404(DonationSubmission.objects.select_related("donor"), pk=pk)

    if request.method == "POST":
        if not request.user.has_perm("donations.change_donationsubmission"):
            messages.error(request, "You do not have permission to change donations.")
            return redirect("donations:detail", pk=pk)
        form = StatusForm(request.POST)
        if form.is_valid():
            submission.status = form.cleaned_data["status"]
            submission.save(update_fields=["status", "updated_at"])
            messages.success(request, f"Status updated to {submission.get_status_display()}.")
            return redirect("donations:detail", pk=pk)
    else:
        form = StatusForm(initial={"status": submission.status})

    return render(request, "donations/donation_detail.html", {
        "submission": submission,
        "form": form,
        "photos": submission.photos.all(),
        "lots": submission.lots.select_related("book"),
    })


@login_required
@permission_required("donations.view_donationphoto", raise_exception=True)
def donation_photo(request, pk):
    """Serve a donor photo only to logged-in staff (NFR-06)."""
    photo = get_object_or_404(DonationPhoto, pk=pk)
    return FileResponse(photo.image.open("rb"))
