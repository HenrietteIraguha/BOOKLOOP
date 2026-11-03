from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render

from .forms import RecipientForm
from .models import Recipient


@login_required
@permission_required("communities.view_recipient", raise_exception=True)
def recipient_list(request):
    """Everyone BookLoop gives books to (FR-10)."""
    recipients = Recipient.objects.annotate(books_received=Sum("distributions__quantity"))

    query = request.GET.get("q", "").strip()
    if query:
        recipients = recipients.filter(
            Q(name__icontains=query) | Q(district__icontains=query)
            | Q(sector__icontains=query) | Q(needs_notes__icontains=query)
        )
    selected_type = request.GET.get("type", "")
    if selected_type:
        recipients = recipients.filter(recipient_type=selected_type)

    return render(request, "communities/recipient_list.html", {
        "recipients": recipients,
        "query": query,
        "types": Recipient.RecipientType.choices,
        "selected_type": selected_type,
    })


@login_required
@permission_required("communities.add_recipient", raise_exception=True)
def recipient_create(request):
    form = RecipientForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        recipient = form.save()
        messages.success(request, f'Recipient "{recipient.name}" added.')
        return redirect("communities:list")
    return render(request, "communities/recipient_form.html", {"form": form, "title": "Add a recipient"})


@login_required
@permission_required("communities.change_recipient", raise_exception=True)
def recipient_edit(request, pk):
    recipient = get_object_or_404(Recipient, pk=pk)
    form = RecipientForm(request.POST or None, instance=recipient)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f'Recipient "{recipient.name}" updated.')
        return redirect("communities:list")
    return render(request, "communities/recipient_form.html", {"form": form, "title": f"Edit {recipient.name}"})
