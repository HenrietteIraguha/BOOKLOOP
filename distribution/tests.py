from django.urls import reverse

from config.testdata import BookLoopTestCase, make_book, make_lot, make_recipient, make_user, setup_roles
from distribution.models import Distribution
from inventory.models import InventoryLot


class DistributionTests(BookLoopTestCase):
    """FR17: recording a distribution reduces the inventory, and never below zero."""

    @classmethod
    def setUpTestData(cls):
        setup_roles()
        cls.operator = make_user("operator1", "Operator")
        cls.lot = make_lot(make_book("Primary 4 English"), quantity=5)
        cls.recipient = make_recipient()

    def setUp(self):
        self.client.force_login(self.operator)

    def give(self, quantity):
        url = reverse("distribution:confirm", args=[self.lot.pk, self.recipient.pk])
        return self.client.post(url, {"quantity": quantity, "distribution_date": "2026-11-20", "notes": ""})

    def test_distribution_reduces_inventory(self):
        self.give(3)
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.quantity, 2)
        record = Distribution.objects.get()
        self.assertEqual(record.recipient, self.recipient)

        self.assertEqual(record.quantity, 3)

    def test_cannot_give_more_than_available(self):
        self.give(9)
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.quantity, 5)
        self.assertEqual(Distribution.objects.count(), 0)

    def test_giving_the_last_copies_marks_the_lot_distributed(self):
        self.give(5)
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.quantity, 0)
        self.assertEqual(self.lot.status, InventoryLot.Status.DISTRIBUTED)
