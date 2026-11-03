from datetime import date

from django import forms


class RecordDistributionForm(forms.Form):
    quantity = forms.IntegerField(label="Number of copies to give", min_value=1)
    distribution_date = forms.DateField(
        label="Date given",
        initial=date.today,
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    notes = forms.CharField(label="Notes (optional)", required=False, widget=forms.Textarea(attrs={"rows": 2}))
