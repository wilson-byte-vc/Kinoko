from django.conf import settings
from django.db import models


def profile_picture_path(instance, filename):
    # Each user's pictures go in their own folder, e.g. media/profile_pics/user_3/me.jpg
    return f"profile_pics/user_{instance.user_id}/{filename}"


class Profile(models.Model):
    # One profile per user. Deleting the user deletes their profile too.
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    picture = models.ImageField(upload_to=profile_picture_path, blank=True)
    display_name = models.CharField(max_length=50, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    interests = models.CharField(
        max_length=200,
        blank=True,
        help_text="Separate interests with commas, e.g. music, hiking, coding",
    )
    bio = models.TextField(max_length=500, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

    @property
    def name(self):
        """The name to show on the site: display name if set, otherwise username."""
        return self.display_name or self.user.username

    def interest_list(self):
        """Turn 'music, hiking ,, coding' into ['music', 'hiking', 'coding']."""
        return [item.strip() for item in self.interests.split(",") if item.strip()]
