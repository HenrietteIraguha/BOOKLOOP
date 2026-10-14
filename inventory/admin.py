from django.contrib import admin

from .models import Book


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "language", "book_type", "education_level", "isbn"]
    list_filter = ["language", "book_type", "education_level", "classification_source"]
    search_fields = ["title", "author", "isbn", "subject"]