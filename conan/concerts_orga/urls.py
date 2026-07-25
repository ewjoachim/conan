from django.urls import path

from . import views

urlpatterns = [
    path("concerts/", views.orga_create, name="o_create"),
    path("concert/<int:pk>/", views.orga_detail, name="o_detail"),
    path("concert/<int:pk>/toggle/", views.orga_toggle, name="o_toggle"),
    path("concert/<int:pk>/yesno/", views.orga_yesno, name="o_yesno"),
    path("concert/<int:pk>/field/", views.orga_field, name="o_field"),
    path("concert/<int:pk>/cotech/", views.orga_cotech_mode, name="o_cotech_mode"),
    path("concert/<int:pk>/meta/", views.orga_meta, name="o_meta"),
    path("concert/<int:pk>/collab/add/", views.collab_add, name="o_collab_add"),
    path(
        "concert/<int:pk>/collab/<int:idx>/delete/",
        views.collab_delete,
        name="o_collab_delete",
    ),
    path(
        "concert/<int:pk>/collab/<int:idx>/update/",
        views.collab_update,
        name="o_collab_update",
    ),
    path(
        "concert/<int:pk>/intervenant/add/",
        views.intervenant_add,
        name="o_intervenant_add",
    ),
    path(
        "concert/<int:pk>/intervenant/<int:idx>/delete/",
        views.intervenant_delete,
        name="o_intervenant_delete",
    ),
    path(
        "concert/<int:pk>/intervenant/<int:idx>/update/",
        views.intervenant_update,
        name="o_intervenant_update",
    ),
    path("concert/<int:pk>/orepet/add/", views.orepet_add, name="o_orepet_add"),
    path(
        "concert/<int:pk>/orepet/<int:idx>/delete/",
        views.orepet_delete,
        name="o_orepet_delete",
    ),
    path(
        "concert/<int:pk>/orepet/<int:idx>/update/",
        views.orepet_update,
        name="o_orepet_update",
    ),
    path("concert/<int:pk>/extra/add/", views.extra_add, name="o_extra_add"),
    path(
        "concert/<int:pk>/extra/<int:idx>/delete/",
        views.extra_delete,
        name="o_extra_delete",
    ),
    path(
        "concert/<int:pk>/extra/<int:idx>/update/",
        views.extra_update,
        name="o_extra_update",
    ),
    path(
        "concert/<int:pk>/extra/<int:idx>/toggle/",
        views.extra_toggle,
        name="o_extra_toggle",
    ),
    path("concert/<int:pk>/archive/", views.orga_archive, name="o_archive"),
    path("concert/<int:pk>/unarchive/", views.orga_unarchive, name="o_unarchive"),
    path("concert/<int:pk>/delete/", views.orga_delete, name="o_delete"),
]
