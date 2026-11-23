from django.urls import reverse

from config.testdata import BookLoopTestCase, make_user, setup_roles


class ReportTests(BookLoopTestCase):
    """FR19: operators can open the reports page."""

    def test_operator_can_view_reports(self):
        setup_roles()
        self.client.force_login(make_user("operator1", "Operator"))
        self.assertEqual(self.client.get(reverse("reports:home")).status_code, 200)
