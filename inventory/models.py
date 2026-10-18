from datetime import date

from django.db import models

class Book(models.Model):
    

    class Language(models.TextChoices):
        KINYARWANDA = "rw", "Kinyarwanda"
        ENGLISH = "en", "English"
        FRENCH = "fr", "French"
        OTHER = "other", "Other"

    class BookType(models.TextChoices):
        TEXTBOOK = "textbook", "Textbook"
        NOVEL = "novel", "Novel"
        CHILDRENS = "childrens", "Children's book"
        REVISION = "revision", "Revision material"
        OTHER = "other", "Other"

    class EducationLevel(models.TextChoices):
        NURSERY = "nursery", "Nursery"
        LOWER_PRIMARY = "lower_primary", "Lower primary (P1-P3)"
        UPPER_PRIMARY = "upper_primary", "Upper primary (P4-P6)"
        LOWER_SECONDARY = "lower_secondary", "Lower secondary (S1-S3)"
        UPPER_SECONDARY = "upper_secondary", "Upper secondary (S4-S6)"
        GENERAL = "general", "General / adult"
        UNKNOWN = "unknown", "Unknown"

    class ClassificationSource(models.TextChoices):
        MANUAL = "manual", "Entered manually"
        TOOL_CONFIRMED = "tool_confirmed", "Suggested by tool, confirmed"
        TOOL_CORRECTED = "tool_corrected", "Suggested by tool, corrected"

    # Identification (FR-01, FR-02)
    isbn = models.CharField("ISBN", max_length=13, blank=True, db_index=True)
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, blank=True)
    publisher = models.CharField(max_length=255, blank=True)

    # Classification (FR-05)
    language = models.CharField(max_length=10, choices=Language.choices)
    book_type = models.CharField(max_length=20, choices=BookType.choices)
    subject = models.CharField(max_length=100, blank=True)
    education_level = models.CharField(
        max_length=20,
        choices=EducationLevel.choices,
        default=EducationLevel.UNKNOWN,
    )

    # Audit trail for classification (NFR-12)
    classification_source = models.CharField(
        max_length=20,
        choices=ClassificationSource.choices,
        default=ClassificationSource.MANUAL,
    )

    # Showcase (FR-20)
    cover_image = models.ImageField(upload_to="covers/", blank=True)
    show_in_showcase = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return self.title



class InventoryLot(models.Model):
    """A group of identical copies of one book, with the same condition.
    Example: 9 copies of 'Primary 4 English' in good condition."""

    class Condition(models.TextChoices):
        NEW = "new", "New"
        GOOD = "good", "Good"
        FAIR = "fair", "Fair (some wear)"
        POOR = "poor", "Poor"

    class Status(models.TextChoices):
        PENDING_ASSESSMENT = "pending_assessment", "Pending assessment"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        IN_STORAGE = "in_storage", "In storage"
        ALLOCATED = "allocated", "Allocated"
        DISTRIBUTED = "distributed", "Distributed"

    # Which book these copies are (FR-01)
    book = models.ForeignKey(Book, on_delete=models.PROTECT, related_name="lots")

    # Condition and quantity (FR-01, FR-08)
    condition = models.CharField(max_length=10, choices=Condition.choices)
    quantity = models.PositiveIntegerField()

    # Where the lot is in the process (FR-07, FR-09)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING_ASSESSMENT,

    )

    storage_location = models.CharField(max_length=100, blank=True)
    date_collected = models.DateField(default=date.today)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date_collected"]

    def __str__(self):
        return f"{self.book.title}: {self.quantity} ({self.get_condition_display()})"