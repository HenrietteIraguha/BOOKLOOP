from django.contrib.auth.models import User
from django.urls import reverse


from config.testdata import PASSWORD, BookLoopTestCase, make_user, setup_roles


class AccessTests(BookLoopTestCase):
    """FR15, FR16, NFR4, NFR5, NFR8: logins, roles and account management."""

    @classmethod
    def setUpTestData(cls):
        setup_roles()
        cls.operator = make_user("operator1", "Operator")
        cls.admin = make_user("admin1", "Administrator")

    def test_internal_pages_need_login(self):
        for name in ["dashboard:home", "inventory:list", "donations:list", "distribution:list", "reports:home"]:
            url = reverse(name)
            response = self.client.get(url)
            self.assertRedirects(response, f"{reverse('login')}?next={url}", msg_prefix=name)

    def test_operator_cannot_open_team_page(self):
        self.client.force_login(self.operator)
        self.assertEqual(self.client.get(reverse("accounts:list")).status_code, 403)

    def test_administrator_can_create_an_operator(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("accounts:list"), {
            "username": "newoperator", "first_name": "", "last_name": "", "email": "",
            "password1": "Strong-pass-2026!", "password2": "Strong-pass-2026!", "role": "Operator",
        })
        user = User.objects.get(username="newoperator")
        self.assertTrue(user.groups.filter(name="Operator").exists())
        self.assertNotEqual(user.password, "Strong-pass-2026!")  # stored hashed
        self.assertTrue(user.check_password("Strong-pass-2026!"))


    def test_administrator_can_deactivate_an_account(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("accounts:update", args=[self.operator.pk]), {"action": "deactivate"})
        self.operator.refresh_from_db()
        self.assertFalse(self.operator.is_active)

    def test_deactivated_user_cannot_log_in(self):
        make_user("gone", "Operator", is_active=False)
        self.assertFalse(self.client.login(username="gone", password=PASSWORD))

    def test_administrator_cannot_deactivate_themselves(self):
        self.client.force_login(self.admin)
        self.client.post(reverse("accounts:update", args=[self.admin.pk]), {"action": "deactivate"})
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)
