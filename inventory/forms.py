from django import forms

from .isbn import normalise_isbn
from .models import Book, InventoryLot


class BookForm(forms.ModelForm):
    """Details of the book title (FR-01, FR-05)."""

    
    isbn = forms.CharField(
        label="ISBN",
        max_length=20,
        required=False,
        help_text="Leave blank if the book has no ISBN.",
    )

    class Meta:
        model = Book
        fields = [
            "isbn", "title", "author", "publisher",
            "language", "book_type", "subject", "education_level",
        ]

    def clean_isbn(self):
        raw = self.cleaned_data.get("isbn", "").strip()
        if not raw:
            return ""
        isbn = normalise_isbn(raw)
        if isbn is None:
            raise forms.ValidationError(
                "This is not a valid ISBN. Check the number, or leave it blank if the book has none."
            )
        return isbn


class LotForm(forms.ModelForm):
    """Details of the physical copies (FR-01, FR-07, FR-08)."""

    status = forms.ChoiceField(
        label="Content readable?",
        choices=[
            (InventoryLot.Status.ACCEPTED, "Yes: accept the books"),
            (InventoryLot.Status.REJECTED, "No: reject (content cannot be read)"),
        ],
        initial=InventoryLot.Status.ACCEPTED,
    )

    class Meta:
        model = InventoryLot
        fields = ["condition", "quantity", "status", "storage_location", "notes"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 2})}

    def clean_quantity(self):
        quantity = self.cleaned_data["quantity"]
        if quantity < 1:
            raise forms.ValidationError("Quantity must be at least 1.")
        return quantity