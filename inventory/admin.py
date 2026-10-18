from django.contrib import admin

from .models import Book, InventoryLot


class InventoryLotInline(admin.TabularInline):
    model = InventoryLot
    extra = 0


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "language", "book_type", "education_level", "isbn"]
    list_filter = ["language", "book_type", "education_level", "classification_source"]
    search_fields = ["title", "author", "isbn", "subject"]
    inlines = [InventoryLotInline]


@admin.register(InventoryLot)
class InventoryLotAdmin(admin.ModelAdmin):
    list_display = ["book", "condition", "quantity", "status", "date_collected"]
    list_filter = ["status", "condition"]
    search_fields = ["book__title", "book__author", "book__isbn"]