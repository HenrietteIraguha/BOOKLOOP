from django.contrib import admin

from .models import DonationPhoto, DonationSubmission, Donor


class DonationPhotoInline(admin.TabularInline):
    model = DonationPhoto
    extra = 0


@admin.register(DonationSubmission)
class DonationSubmissionAdmin(admin.ModelAdmin):
    list_display = ["donor", "number_of_books", "language", "status", "submitted_at"]
    list_filter = ["status", "language"]
    search_fields = ["donor__name", "donor__phone", "donor__area", "book_types"]
    inlines = [DonationPhotoInline]


@admin.register(Donor)
class DonorAdmin(admin.ModelAdmin):
    list_display = ["name", "phone", "email", "area"]
    search_fields = ["name", "phone", "email", "area"]