from django.shortcuts import render

# Create your views here.


# ---- Team accounts: Administrators manage accounts and roles (FR16, NFR5) ----
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group, User
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

ROLES = ["Operator", "Administrator"]


def _role_of(user):
    if user.is_superuser:
        return "Owner"
    names = [g.name for g in user.groups.all() if g.name in ROLES]
    return ", ".join(names) or "No role"


class NewAccountForm(UserCreationForm):
    role = forms.ChoiceField(choices=[(r, r) for r in ROLES])

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email")


@login_required

@permission_required("auth.view_user", raise_exception=True)
def account_list(request):
    form = NewAccountForm()
    if request.method == "POST":
        if not request.user.has_perm("auth.add_user"):
            raise PermissionDenied
        form = NewAccountForm(request.POST)
        if form.is_valid():
            user = form.save()  # the password is stored hashed (NFR8)
            user.groups.set([Group.objects.get(name=form.cleaned_data["role"])])
            messages.success(request, f"Account “{user.username}” created as {form.cleaned_data['role']}.")
            return redirect("accounts:list")

    users = User.objects.order_by("-is_active", "username").prefetch_related("groups")
    rows = [{"user": u, "role": _role_of(u)} for u in users]
    return render(request, "accounts/account_list.html", {"rows": rows, "form": form, "roles": ROLES})


@login_required
@permission_required("auth.change_user", raise_exception=True)
@require_POST
def account_update(request, pk):
    target = get_object_or_404(User, pk=pk)
    action = request.POST.get("action")

    if target.is_superuser:
        messages.error(request, "The owner account cannot be changed here.")
    elif target == request.user:
        messages.error(request, "You cannot change your own role or deactivate your own account.")
    elif action == "set_role" and request.POST.get("role") in ROLES:
        role = request.POST["role"]
        target.groups.set([Group.objects.get(name=role)])

        messages.success(request, f"“{target.username}” is now {role}.")
    elif action == "deactivate":
        target.is_active = False
        target.save(update_fields=["is_active"])
        messages.success(request, f"“{target.username}” was deactivated and can no longer log in. Their records are kept.")
    elif action == "activate":
        target.is_active = True
        target.save(update_fields=["is_active"])
        messages.success(request, f"“{target.username}” can log in again.")
    else:
        messages.error(request, "That change is not possible.")
    return redirect("accounts:list")
