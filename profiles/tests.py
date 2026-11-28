import shutil
import tempfile
from datetime import date, timedelta
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import Profile

# Uploaded pictures in tests go to a throwaway folder, not the real media/ folder
TEST_MEDIA = tempfile.mkdtemp()


def make_image(name="me.png"):
    buffer = BytesIO()
    Image.new("RGB", (10, 10), "orange").save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


@override_settings(MEDIA_ROOT=TEST_MEDIA)
class ProfileTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEST_MEDIA, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.user = get_user_model().objects.create_user(username="aiko")
        self.client.force_login(self.user)

    def test_no_one_signed_in_shows_message(self):
        self.client.logout()
        for url in (reverse("profile"), reverse("profile_edit")):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "No one is signed in yet")

        # Saving while signed out does nothing
        self.client.post(reverse("profile_edit"), {"display_name": "Sneaky"})
        self.assertFalse(Profile.objects.exists())

    def test_profile_is_created_on_first_visit(self):
        self.assertFalse(Profile.objects.filter(user=self.user).exists())
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Profile.objects.filter(user=self.user).exists())
        # No display name yet, so the username is shown
        self.assertContains(response, "aiko")

    def test_edit_saves_everything(self):
        response = self.client.post(reverse("profile_edit"), {
            "display_name": "Aiko T.",
            "date_of_birth": "2004-05-17",
            "interests": "music, hiking ,, coding",
            "bio": "Hello from MMU!",
            "picture": make_image(),
        })
        self.assertRedirects(response, reverse("profile"))

        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.display_name, "Aiko T.")
        self.assertEqual(profile.date_of_birth, date(2004, 5, 17))
        self.assertEqual(profile.interest_list(), ["music", "hiking", "coding"])
        self.assertEqual(profile.bio, "Hello from MMU!")
        self.assertTrue(profile.picture.name.startswith(f"profile_pics/user_{self.user.id}/"))

        page = self.client.get(reverse("profile"))
        self.assertContains(page, "Aiko T.")
        self.assertContains(page, '<span class="chip">hiking</span>', html=True)
        self.assertContains(page, profile.picture.url)

    def test_new_picture_replaces_old_file(self):
        self.client.post(reverse("profile_edit"), {"picture": make_image("first.png")})
        old = Profile.objects.get(user=self.user).picture
        old_name, storage = old.name, old.storage

        self.client.post(reverse("profile_edit"), {"picture": make_image("second.png")})
        new = Profile.objects.get(user=self.user).picture
        self.assertIn("second", new.name)
        self.assertFalse(storage.exists(old_name))  # old file cleaned up
        self.assertTrue(storage.exists(new.name))

    def test_remove_picture(self):
        self.client.post(reverse("profile_edit"), {"picture": make_image()})
        picture = Profile.objects.get(user=self.user).picture
        old_name, storage = picture.name, picture.storage

        self.client.post(reverse("profile_edit"), {"remove_picture": "on"})
        self.assertFalse(Profile.objects.get(user=self.user).picture)
        self.assertFalse(storage.exists(old_name))

    def test_saving_other_fields_keeps_picture(self):
        self.client.post(reverse("profile_edit"), {"picture": make_image()})
        name = Profile.objects.get(user=self.user).picture.name

        self.client.post(reverse("profile_edit"), {"display_name": "New name"})
        profile = Profile.objects.get(user=self.user)
        self.assertEqual(profile.picture.name, name)
        self.assertTrue(profile.picture.storage.exists(name))

    def test_future_date_of_birth_is_rejected(self):
        tomorrow = date.today() + timedelta(days=1)
        response = self.client.post(reverse("profile_edit"), {"date_of_birth": tomorrow.isoformat()})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "can&#x27;t be in the future")
        self.assertIsNone(Profile.objects.get(user=self.user).date_of_birth)

    def test_non_image_file_is_rejected(self):
        fake = SimpleUploadedFile("virus.png", b"not really an image", content_type="image/png")
        response = self.client.post(reverse("profile_edit"), {"picture": fake})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Profile.objects.get(user=self.user).picture)

    def test_users_only_see_their_own_profile(self):
        other = get_user_model().objects.create_user(username="ben")
        Profile.objects.create(user=other, display_name="Ben's secret name")
        response = self.client.get(reverse("profile"))
        self.assertNotContains(response, "Ben&#x27;s secret name")
