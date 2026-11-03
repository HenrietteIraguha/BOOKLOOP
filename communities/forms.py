from django import forms

from .models import Recipient


class RecipientForm(forms.ModelForm):
    class Meta:
        model = Recipient
        fields = [
            "name", "recipient_type", "district", "sector",
            "contact_person", "contact_phone", "needs_notes", "date_identified",
        ]
        widgets = {
            "needs_notes": forms.Textarea(attrs={"rows": 3}),
            "date_identified": forms.DateInput(attrs={"type": "date"}),
        }
