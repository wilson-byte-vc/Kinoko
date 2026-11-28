from django.contrib import messages
from django.shortcuts import redirect, render

from .forms import ProfileForm
from .models import Profile


def get_profile(user):
    # Make the profile the first time someone needs it, so every user has one.
    profile, _ = Profile.objects.get_or_create(user=user)
    return profile


def profile_view(request):
    # A profile belongs to a user, so with no one logged in there is nothing to show.
    if not request.user.is_authenticated:
        return render(request, "profiles/no_user.html")

    return render(request, "profiles/profile.html", {"profile": get_profile(request.user)})


def profile_edit(request):
    if not request.user.is_authenticated:
        return render(request, "profiles/no_user.html")

    profile = get_profile(request.user)

    if request.method == "POST":
        # request.FILES carries the uploaded picture
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile saved.")
            return redirect("profile")
    else:
        form = ProfileForm(instance=profile)

    return render(request, "profiles/profile_edit.html", {"form": form, "profile": profile})
