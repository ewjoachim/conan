from django.urls import path

from . import views

urlpatterns = [
    path("login/", views.login_page, name="login"),
    path("auth/google/", views.google_callback, name="google_callback"),
    path("logout/", views.logout_view, name="logout"),
]
