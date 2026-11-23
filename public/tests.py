from django.urls import reverse

from config.testdata import BookLoopTestCase, make_book
from donations.models import DonationSubmission, Donor


def donation_data(**changes):
    data = {
        "name": "Aline Uwase", "phone": "0788000000", "email": "", "area": "Kimironko",
        "number_of_books": "12", "book_types": "Primary textbooks", "language": "en",
        "condition": "good", "message": "", "consent": "on", "website": "",
    }
    data.update(changes)
    return data


class DonationFormTests(BookLoopTestCase):
    """FR12: donors submit donations through a public form, without an account."""

    def test_donor_can_submit_without_an_account(self):
        response = self.client.post(reverse("public:donate"), donation_data())
        self.assertRedirects(response, reverse("public:donate_thanks"))
        submission = DonationSubmission.objects.get()
        self.assertEqual(submission.number_of_books, 12)
        self.assertEqual(submission.status, DonationSubmission.Status.PENDING)
        self.assertEqual(submission.donor.name, "Aline Uwase")

    def test_consent_is_required(self):
        data = donation_data()
        data.pop("consent")
        self.client.post(reverse("public:donate"), data)

        self.assertEqual(DonationSubmission.objects.count(), 0)

    def test_phone_or_email_is_required(self):
        self.client.post(reverse("public:donate"), donation_data(phone="", email=""))
        self.assertEqual(DonationSubmission.objects.count(), 0)

    def test_spam_trap_blocks_bots(self):
        self.client.post(reverse("public:donate"), donation_data(website="http://spam.example"))
        self.assertEqual(DonationSubmission.objects.count(), 0)

    def test_returning_donor_is_reused(self):
        self.client.post(reverse("public:donate"), donation_data())
        self.client.post(reverse("public:donate"), donation_data(number_of_books="3"))
        self.assertEqual(Donor.objects.count(), 1)
        self.assertEqual(DonationSubmission.objects.count(), 2)


class ShowcaseTests(BookLoopTestCase):
    """FR20: the homepage shows only books that staff approved."""

    def test_homepage_shows_only_approved_books(self):
        make_book("Approved Book", show_in_showcase=True)
        make_book("Hidden Book")
        response = self.client.get(reverse("public:home"))
        self.assertContains(response, "Approved Book")
        self.assertNotContains(response, "Hidden Book")
