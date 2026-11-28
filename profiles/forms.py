from datetime import date

from django import forms

from .models import Profile

MAX_PICTURE_MB = 5


class ProfileForm(forms.ModelForm):
    remove_picture = forms.BooleanField(required=False, label="Remove current picture")

    class Meta:
        model = Profile
        fields = ["picture", "display_name", "date_of_birth", "interests", "bio"]
        labels = {
            "picture": "Profile picture",
            "date_of_birth": "Date of birth",
        }
        widgets = {
            "picture": forms.FileInput(attrs={"accept": "image/*"}),
            # type="date" gives the browser's built-in date picker
            "date_of_birth": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "display_name": forms.TextInput(attrs={"placeholder": "What should people call you?"}),
            "interests": forms.TextInput(attrs={"placeholder": "music, hiking, coding"}),
            "bio": forms.Textarea(attrs={"rows": 4, "placeholder": "Tell people a bit about yourself"}),
        }

    field_order = ["picture", "remove_picture", "display_name", "date_of_birth", "interests", "bio"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remember the picture saved before this edit, so we can clean it up
        self.old_picture_name = self.instance.picture.name if self.instance.picture else ""

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get("date_of_birth")
        if dob and dob > date.today():
            raise forms.ValidationError("Date of birth can't be in the future.")
        return dob

    def clean_picture(self):
        picture = self.cleaned_data.get("picture")
        # Only check size for a newly uploaded file (not the one already saved)
        if picture and hasattr(picture, "content_type"):
            if picture.size > MAX_PICTURE_MB * 1024 * 1024:
                raise forms.ValidationError(f"Picture must be smaller than {MAX_PICTURE_MB} MB.")
        return picture

    def save(self, commit=True):
        profile = super().save(commit=False)
        uploaded_new = "picture" in self.changed_data

        if self.cleaned_data.get("remove_picture") and not uploaded_new:
            profile.picture = None

        if commit:
            profile.save()
            # Delete the old picture file if it was replaced or removed
            if self.old_picture_name and profile.picture.name != self.old_picture_name:
                profile.picture.storage.delete(self.old_picture_name)
        return profile
