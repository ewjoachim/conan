from django.urls import path

from . import views

urlpatterns = [
    path("healthz", views.healthz, name="healthz"),
    path("", views.concert_list, name="list"),
    path("concerts/", views.concert_create, name="create"),
    path("concert/<int:pk>/", views.concert_detail, name="detail"),
    path("concert/<int:pk>/toggle/", views.toggle, name="toggle"),
    path("concert/<int:pk>/yesno/", views.set_yesno, name="yesno"),
    path("concert/<int:pk>/field/", views.set_field, name="field"),
    path("concert/<int:pk>/cotech-mode/", views.set_cotech_mode, name="cotech_mode"),
    path("concert/<int:pk>/meta/", views.update_meta, name="meta"),
    path("concert/<int:pk>/repet/add/", views.repet_add, name="repet_add"),
    path(
        "concert/<int:pk>/repet/<int:idx>/delete/",
        views.repet_delete,
        name="repet_delete",
    ),
    path(
        "concert/<int:pk>/repet/<int:idx>/update/",
        views.repet_update,
        name="repet_update",
    ),
    path("concert/<int:pk>/extra/add/", views.extra_add, name="extra_add"),
    path(
        "concert/<int:pk>/extra/<int:idx>/delete/",
        views.extra_delete,
        name="extra_delete",
    ),
    path(
        "concert/<int:pk>/extra/<int:idx>/update/",
        views.extra_update,
        name="extra_update",
    ),
    path(
        "concert/<int:pk>/extra/<int:idx>/toggle/",
        views.extra_toggle,
        name="extra_toggle",
    ),
    path("concert/<int:pk>/archive/", views.concert_archive, name="archive"),
    path("concert/<int:pk>/unarchive/", views.concert_unarchive, name="unarchive"),
    path("concert/<int:pk>/delete/", views.concert_delete, name="delete"),
    path("archives/", views.concert_archives, name="archives"),
]
