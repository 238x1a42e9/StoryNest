from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import SignUpForm


def register(request):
    if request.user.is_authenticated:
        return redirect("blog:home")
    next_url = request.POST.get("next") or request.GET.get("next", "")
    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"Welcome, {user.get_username()}.")
        if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
            return redirect(next_url)
        return redirect("blog:create" if user.has_perm("blog.add_post") else "blog:home")
    return render(request, "registration/register.html", {"form": form, "next": next_url})
