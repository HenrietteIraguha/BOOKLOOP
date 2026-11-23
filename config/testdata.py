"""Shared helpers for BookLoop's automated tests."""
from datetime import date
from io import StringIO

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import TestCase, override_settings

from communities.models import Recipient
from inventory.models import Book, InventoryLot

# Tests keep uploaded files in memory (nothing goes to Cloudinary) and use plain
# static files (no collectstatic manifest needed).
TEST_STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}
PASSWORD = "test-pass-2026!"


@override_settings(STORAGES=TEST_STORAGES)
class BookLoopTestCase(TestCase):
    pass


def setup_roles():
    call_command("setup_roles", stdout=StringIO())


def make_user(username, role=None, **extra):
    user = User.objects.create_user(username=username, password=PASSWORD, **extra)

    if role:
        user.groups.add(Group.objects.get(name=role))
    return user


def _fill_required(model, data):
    """Give required choice and date fields a valid value, so tests don't depend on every field."""
    for f in model._meta.concrete_fields:
        if f.name in data or f.primary_key or f.null or f.has_default():
            continue
        if f.is_relation or getattr(f, "auto_now", False) or getattr(f, "auto_now_add", False):
            continue
        if f.choices:
            data[f.name] = f.choices[0][0]
        elif f.get_internal_type() == "DateField":
            data[f.name] = date.today()
    return data


def make_book(title="Primary 4 English", **extra):
    return Book.objects.create(**_fill_required(Book, {"title": title, **extra}))


def make_lot(book, quantity=5, status=InventoryLot.Status.ACCEPTED, **extra):
    data = {"book": book, "quantity": quantity, "status": status, **extra}
    return InventoryLot.objects.create(**_fill_required(InventoryLot, data))


def make_recipient(name="Gasabo Lending Shelf", **extra):
    return Recipient.objects.create(**_fill_required(Recipient, {"name": name, **extra}))
