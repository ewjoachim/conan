from django.urls import include, path

urlpatterns = [
    path("", include("conan.accounts.urls")),
    path("", include("conan.concerts.urls")),
    path("orga/", include("conan.concerts_orga.urls")),
]
