from django.urls import path

from . import views

urlpatterns = [
    path("signup/", views.signup),
    path("login/", views.login),
    path("logout/", views.logout),
    path("me/", views.me),
    path("password-reset/", views.password_reset),
]
