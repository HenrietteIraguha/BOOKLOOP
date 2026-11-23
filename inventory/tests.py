from django.urls import reverse

from config.testdata import BookLoopTestCase, make_book, make_lot, make_user, setup_roles
from inventory.models import InventoryLot, StatusHistory


class LotStatusTests(BookLoopTestCase):
    """FR9: operators update a lot's status; every change is logged."""

    @classmethod
    def setUpTestData(cls):
        setup_roles()
        cls.operator = make_user("operator1", "Operator")

        cls.lot = make_lot(make_book("Primary 4 English"))

    def setUp(self):
        self.client.force_login(self.operator)

    def test_operator_can_move_a_lot_to_storage(self):
        self.client.post(reverse("inventory:lot_status", args=[self.lot.pk]), {"status": "in_storage"})
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.status, InventoryLot.Status.IN_STORAGE)
        self.assertTrue(StatusHistory.objects.filter(
            lot=self.lot, new_status=InventoryLot.Status.IN_STORAGE, changed_by=self.operator).exists())

    def test_distributed_cannot_be_set_by_hand(self):
        self.client.post(reverse("inventory:lot_status", args=[self.lot.pk]), {"status": "distributed"})
        self.lot.refresh_from_db()
        self.assertEqual(self.lot.status, InventoryLot.Status.ACCEPTED)


class SearchTests(BookLoopTestCase):
    """FR18: search the inventory."""

    @classmethod
    def setUpTestData(cls):
        setup_roles()
        cls.operator = make_user("operator1", "Operator")
        make_lot(make_book("Primary 4 English"))

    def test_search_finds_books_by_title(self):
        self.client.force_login(self.operator)
        self.assertContains(self.client.get(reverse("inventory:list"), {"q": "Primary"}), "Primary 4 English")
        self.assertNotContains(self.client.get(reverse("inventory:list"), {"q": "zzzz"}), "Primary 4 English")
