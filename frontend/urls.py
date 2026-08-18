from django.urls import path

from frontend.views import (
    home_page,
    login_page,
    register_page,
    dashboard,
)


urlpatterns = [
    path("", home_page, name="home"),

    path("login/", login_page, name="login"),

    path("register/", register_page, name="register"),

    path("dashboard/", dashboard, name="dashboard"),
]