from django.urls import path

from . import views

urlpatterns = [
    path("", views.concert_list, name="list"),
    path("concerts/", views.concert_create, name="create"),
    path("concert/<int:pk>/", views.concert_detail, name="detail"),
    path("concert/<int:pk>/toggle/", views.toggle, name="toggle"),
    path("concert/<int:pk>/yesno/", views.set_yesno, name="yesno"),
    path("concert/<int:pk>/field/", views.set_field, name="field"),
    path("concert/<int:pk>/cotech-mode/", views.set_cotech_mode, name="cotech_mode"),
    path("concert/<int:pk>/meta/", views.update_meta, name="meta"),
]
