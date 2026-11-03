from datetime import date

from django.db import models


class Recipient(models.Model):
    """Whoever receives books for children: a household, a community group,
    or a school running take-home lending (FR-10).
    Children themselves are never stored; only an adult contact person."""

    class RecipientType(models.TextChoices):
        HOUSEHOLD = "household", "Household / family"
        COMMUNITY_GROUP = "community_group", "Community group or reading space"
        SCHOOL_LENDING = "school_lending", "School (take-home lending)"
        OTHER = "other", "Other"

    name = models.CharField(max_length=150)
    recipient_type = models.CharField(max_length=20, choices=RecipientType.choices)
    district = models.CharField(max_length=100)
    sector = models.CharField(max_length=100, blank=True)
    contact_person = models.CharField(max_length=150, help_text="An adult: parent, guardian, teacher or group leader.")
    contact_phone = models.CharField(max_length=30, blank=True)
    needs_notes = models.TextField(
        blank=True,
        help_text="For example: children aged 6-9, prefer Kinyarwanda storybooks.",
    )
    date_identified = models.DateField(default=date.today)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name
