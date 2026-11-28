from django.contrib import admin

from .models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "display_name", "date_of_birth", "updated_at")
    search_fields = ("user__username", "display_name", "interests")
