from django import forms

from .images import ImageCheckError, check_and_clean_image
from .models import DonationSubmission

MAX_PHOTOS = 5


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleImageField(forms.FileField):
    """Accepts several photos and checks each one."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(attrs={"accept": "image/jpeg,image/png,image/webp"}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        if not data:
            if self.required:
                raise forms.ValidationError("Please add at least one photo.")
            return []
        files = data if isinstance(data, (list, tuple)) else [data]
        if len(files) > MAX_PHOTOS:
            raise forms.ValidationError(f"Please upload at most {MAX_PHOTOS} photos.")
        cleaned = []
        for uploaded in files:
            try:
                cleaned.append(check_and_clean_image(uploaded))
            except ImageCheckError as error:
                raise forms.ValidationError(str(error))
        return cleaned


class DonationForm(forms.Form):
    """The public donation form (FR-12). No account needed."""

    name = forms.CharField(label="Your name", max_length=150)
    phone = forms.CharField(label="Phone number", max_length=30, required=False)
    email = forms.EmailField(label="Email address", required=False)
    area = forms.CharField(
        label="Your area",
        max_length=150,
        help_text="District and sector, so we can arrange to collect the books.",
    )
    number_of_books = forms.IntegerField(label="About how many books?", min_value=1, max_value=1000)
    book_types = forms.CharField(
        label="What kinds of books?",
        max_length=255,
        help_text="For example: P4 textbooks, storybooks, novels.",
    )
    language = forms.ChoiceField(label="Main language of the books", choices=DonationSubmission.Language.choices)
    condition = forms.ChoiceField(
        label="General condition",
        choices=DonationSubmission.Condition.choices,
        initial=DonationSubmission.Condition.UNSURE,
    )
    message = forms.CharField(label="Message (optional)", required=False, widget=forms.Textarea(attrs={"rows": 3}))
    photos = MultipleImageField(
        label="Photos of the books (optional)",
        required=False,
        help_text="Up to 5 photos; JPEG, PNG or WebP; 5 MB each at most. "
                  "Location information is removed from photos before they are saved.",
    )
    consent = forms.BooleanField(
        label="I agree that BookLoop may use my contact details and photos only to arrange this donation. "
              "They will not be shown publicly.",
        required=True,
        error_messages={"required": "Please tick this box so we can contact you about your donation."},
    )
    website = forms.CharField(required=False, widget=forms.TextInput(attrs={"tabindex": "-1", "autocomplete": "off"}))

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("website"):
            raise forms.ValidationError("Your submission could not be accepted.")
        if not cleaned.get("phone") and not cleaned.get("email"):
            raise forms.ValidationError("Please give a phone number or an email address so we can contact you.")
        return cleaned