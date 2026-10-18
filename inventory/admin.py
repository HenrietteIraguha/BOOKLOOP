from django.contrib import admin

from .models import Book, InventoryLot, StatusHistory


class InventoryLotInline(admin.TabularInline):

    model = InventoryLot
    extra = 0
    can_delete = False  # Lots are never deleted; change their status instead.


class StatusHistoryInline(admin.TabularInline):

    model = StatusHistory
    extra = 0
    can_delete = False
    readonly_fields = ["changed_at", "changed_by", "old_status", "new_status"]

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "language", "book_type", "education_level", "isbn"]
    list_filter = ["language", "book_type", "education_level", "classification_source"]
    search_fields = ["title", "author", "isbn", "subject"]
    inlines = [InventoryLotInline]

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            instance._changed_by = request.user
            instance.save()
        formset.save_m2m()


@admin.register(InventoryLot)
class InventoryLotAdmin(admin.ModelAdmin):
    list_display = ["book", "condition", "quantity", "status", "date_collected"]
    list_filter = ["status", "condition"]
    search_fields = ["book__title", "book__author", "book__isbn"]
    inlines = [StatusHistoryInline]

    def save_model(self, request, obj, form, change):
        obj._changed_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):

    list_display = ["changed_at", "lot", "old_status", "new_status", "changed_by"]
    list_filter = ["new_status", "changed_by"]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False