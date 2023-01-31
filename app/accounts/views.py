from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import HttpResponseRedirect

from .forms import RegisterForm, LoginForm

def register_user(request):

    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse("core:index"))
    else:

        form = RegisterForm()

        if request.method == "POST":
            form = RegisterForm(request.POST)
            if form.is_valid():

                form.save()
            
        context = {"form": form}

        return render(request, "accounts/register.html", context)




