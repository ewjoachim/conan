from django.urls import include, path

urlpatterns = [
    path("", include("conan.concerts.urls")),
]
