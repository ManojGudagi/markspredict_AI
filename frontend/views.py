from django.shortcuts import render
from django.views.decorators.cache import never_cache


def home_page(request):
    return render(request, "index.html")


def login_page(request):
    return render(request, "login.html")


def register_page(request):
    return render(request, "register.html")


@never_cache
def dashboard(request):
    return render(request, "dashboard.html")
