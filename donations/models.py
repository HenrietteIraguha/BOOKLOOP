from django.db import models


class Donor(models.Model):
    """A person who donates books. Stored once, even if they donate again."""

    name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    area = models.CharField("Area or location", max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class DonationSubmission(models.Model):
    """One completed public donation form (FR-12, FR-13)."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        CONTACTED = "contacted", "Contacted"
        COLLECTED = "collected", "Collected"
        CLOSED = "closed", "Closed"
        REJECTED = "rejected", "Rejected"

    class Language(models.TextChoices):
        KINYARWANDA = "rw", "Kinyarwanda"
        ENGLISH = "en", "English"

        FRENCH = "fr", "French"
        MIXED = "mixed", "Mixed languages"
        OTHER = "other", "Other"

    class Condition(models.TextChoices):
        GOOD = "good", "Mostly good"
        MIXED = "mixed", "Mixed"
        WORN = "worn", "Mostly worn"
        UNSURE = "unsure", "Not sure"

    donor = models.ForeignKey(Donor, on_delete=models.PROTECT, related_name="submissions")
    number_of_books = models.PositiveIntegerField()
    book_types = models.CharField(
        max_length=255,
        help_text="For example: P4 textbooks, storybooks, novels",
    )
    language = models.CharField(max_length=10, choices=Language.choices)
    condition = models.CharField(max_length=10, choices=Condition.choices, default=Condition.UNSURE)
    message = models.TextField(blank=True)
    consent_given = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, db_index=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-submitted_at"]

    def __str__(self):
        return f"{self.donor}: {self.number_of_books} books ({self.submitted_at:%d %b %Y})"


class DonationPhoto(models.Model):


    submission = models.ForeignKey(
        DonationSubmission,
        on_delete=models.CASCADE,  
        related_name="photos",
    )
    image = models.ImageField(upload_to="donations/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo for {self.submission}"