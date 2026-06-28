"""Server-driven HTMX views.

Each mutating view performs a read-modify-write of ``Concert.state`` inside a
single ``transaction.atomic()`` block. Combined with SQLite's IMMEDIATE
transaction mode (see settings), writers serialize, so concurrent toggles can't
clobber each other's updates to the shared JSON blob.

Most mutations re-render the affected *step* (``hx-target`` is its container) and
piggy-back an out-of-band swap of the header progress bar. Free-text saves are
silent (HTTP 204) so the user's textarea keeps focus while typing.
"""

# login_not_required exists since Django 5.1 (our floor is 5.2); the django-types
# stubs lag behind, so silence ty's import error here.
from typing import Any

from django.contrib.auth.decorators import (
    login_not_required,  # ty: ignore[unresolved-import]
    login_required,
)
from django.db import connection, transaction
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from . import checklist
from .models import Concert

META_FIELDS = frozenset(["name", "date", "respo", "mandataire"])


@login_not_required
def healthz(request: HttpRequest) -> HttpResponse:
    """Liveness probe for the container healthcheck.

    A failing probe makes ``podman auto-update`` roll back to the previous
    image, so this must catch a broken release: it verifies the app booted and
    that SQLite is reachable. No auth, no side effects.
    """
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return HttpResponse("ok", content_type="text/plain")


def concert_list(request: HttpRequest) -> HttpResponse:
    concerts = Concert.objects.filter(archived=False)
    html = render_to_string(
        "concerts/list.html.jinja",
        {"concerts": concerts, "count": concerts.count()},
        request,
    )
    return HttpResponse(html)


def concert_archives(request: HttpRequest) -> HttpResponse:
    concerts = Concert.objects.filter(archived=True)
    html = render_to_string(
        "concerts/archives.html.jinja",
        {"concerts": concerts, "count": concerts.count()},
        request,
    )
    return HttpResponse(html)


@require_POST
def concert_create(request: HttpRequest) -> HttpResponse:
    from datetime import date as parse_date

    raw_date = request.POST.get("date", "").strip()
    try:
        parsed_date = parse_date.fromisoformat(raw_date) if raw_date else None
    except ValueError:
        parsed_date = None
    concert = Concert.objects.create(
        name=request.POST.get("name", "").strip(),
        date=parsed_date,
        respo=request.POST.get("respo", "").strip(),
    )
    return redirect("detail", pk=concert.pk)


def concert_detail(request: HttpRequest, pk: int) -> HttpResponse:
    concert = get_object_or_404(Concert, pk=pk)
    html = render_to_string(
        "concerts/detail.html.jinja",
        {
            "concert": concert,
            "steps": checklist.STEPS,
            "state": concert.state,
            "progress": checklist.compute_progress(concert.state),
        },
        request,
    )
    return HttpResponse(html)


def _render_step_and_progress(
    request: HttpRequest, concert: Concert, step: checklist.Step
) -> str:
    """Re-render one step plus an out-of-band progress-bar swap."""
    context = {"concert": concert, "step": step, "state": concert.state}
    step_html = render_to_string("concerts/partials/step.html.jinja", context, request)
    progress_html = render_to_string(
        "concerts/partials/progress.html.jinja",
        {"progress": checklist.compute_progress(concert.state), "oob": True},
        request,
    )
    return step_html + progress_html


@require_POST
def toggle(request: HttpRequest, pk: int) -> HttpResponse:
    key = request.POST.get("key", "")
    step_id = request.POST.get("step", "")
    if key not in checklist.TOGGLE_KEYS or step_id not in checklist.STEPS_BY_ID:
        return HttpResponseBadRequest("unknown key or step")

    with transaction.atomic():
        concert = get_object_or_404(Concert, pk=pk)
        concert.state[key] = not concert.state.get(key, False)
        concert.progress = checklist.compute_progress(concert.state).pct
        concert.save(update_fields=["state", "progress", "updated_at"])
        step = checklist.STEPS_BY_ID[step_id]
        return HttpResponse(_render_step_and_progress(request, concert, step))


@require_POST
def set_yesno(request: HttpRequest, pk: int) -> HttpResponse:
    item_id = request.POST.get("item_id", "")
    val = request.POST.get("val", "")
    step_id = request.POST.get("step", "")
    if (
        item_id not in checklist.YESNO_IDS
        or val not in {"y", "n"}
        or step_id not in checklist.STEPS_BY_ID
    ):
        return HttpResponseBadRequest("invalid yes/no")

    with transaction.atomic():
        concert = get_object_or_404(Concert, pk=pk)
        concert.state[f"yn_{item_id}"] = val
        concert.progress = checklist.compute_progress(concert.state).pct
        concert.save(update_fields=["state", "progress", "updated_at"])
        step = checklist.STEPS_BY_ID[step_id]
        return HttpResponse(_render_step_and_progress(request, concert, step))


@require_POST
def set_cotech_mode(request: HttpRequest, pk: int) -> HttpResponse:
    mode = request.POST.get("mode", "")
    step_id = request.POST.get("step", "")
    if mode not in checklist.COTECH_MODES or step_id not in checklist.STEPS_BY_ID:
        return HttpResponseBadRequest("invalid cotech mode")

    with transaction.atomic():
        concert = get_object_or_404(Concert, pk=pk)
        concert.state["cotech_mode"] = mode
        concert.progress = checklist.compute_progress(concert.state).pct
        concert.save(update_fields=["state", "progress", "updated_at"])
        step = checklist.STEPS_BY_ID[step_id]
        return HttpResponse(_render_step_and_progress(request, concert, step))


@require_POST
def set_field(request: HttpRequest, pk: int) -> HttpResponse:
    """Save a free-text field. Text alone doesn't change progress, so reply 204."""
    key = request.POST.get("key", "")
    if key not in checklist.TEXT_KEYS:
        return HttpResponseBadRequest("unknown field")

    with transaction.atomic():
        concert = get_object_or_404(Concert, pk=pk)
        concert.state[key] = request.POST.get("text", "")
        concert.save(update_fields=["state", "updated_at"])
    return HttpResponse(status=204)


@require_POST
def update_meta(request: HttpRequest, pk: int) -> HttpResponse:
    """Update one metadata column. Returns an OOB title swap when the name changes."""
    field = request.POST.get("field", "")
    if field not in META_FIELDS:
        return HttpResponseBadRequest("unknown field")

    concert = get_object_or_404(Concert, pk=pk)
    value: Any = request.POST.get("value", "").strip()
    if field == "date":
        from datetime import date as date_type

        value = date_type.fromisoformat(value) if value else None
    setattr(concert, field, value)
    concert.save(update_fields=[field, "updated_at"])

    if field == "name":
        html = render_to_string(
            "concerts/partials/title.html.jinja",
            {"concert": concert, "oob": True},
            request,
        )
        return HttpResponse(html)
    return HttpResponse(status=204)


def _render_step(request: HttpRequest, concert: Concert, step_id: str) -> HttpResponse:
    step = checklist.STEPS_BY_ID[step_id]
    return HttpResponse(_render_step_and_progress(request, concert, step))


@require_POST
def repet_add(request: HttpRequest, pk: int) -> HttpResponse:
    step_id = request.POST.get("step", "")
    if step_id not in checklist.STEPS_BY_ID:
        return HttpResponseBadRequest("unknown step")
    with transaction.atomic():
        concert = get_object_or_404(Concert, pk=pk)
        repets: list[dict[str, str | None]] = list(concert.state.get("repets", []))
        repets.append({"date": None, "lieu": ""})
        concert.state["repets"] = repets
        concert.save(update_fields=["state", "updated_at"])
    return _render_step(request, concert, step_id)


@require_POST
def repet_delete(request: HttpRequest, pk: int, idx: int) -> HttpResponse:
    step_id = request.POST.get("step", "")
    if step_id not in checklist.STEPS_BY_ID:
        return HttpResponseBadRequest("unknown step")
    with transaction.atomic():
        concert = get_object_or_404(Concert, pk=pk)
        repets = list(concert.state.get("repets", []))
        if 0 <= idx < len(repets):
            repets.pop(idx)
        concert.state["repets"] = repets
        concert.save(update_fields=["state", "updated_at"])
    return _render_step(request, concert, step_id)


@require_POST
def repet_update(request: HttpRequest, pk: int, idx: int) -> HttpResponse:
    with transaction.atomic():
        concert = get_object_or_404(Concert, pk=pk)
        repets = list(concert.state.get("repets", []))
        if 0 <= idx < len(repets):
            repet = dict(repets[idx])
            if "date" in request.POST:
                repet["date"] = request.POST["date"].strip() or None
            if "lieu" in request.POST:
                repet["lieu"] = request.POST["lieu"].strip()
            repets[idx] = repet
        concert.state["repets"] = repets
        concert.save(update_fields=["state", "updated_at"])
    return HttpResponse(status=204)


@require_POST
@login_required
def concert_archive(request: HttpRequest, pk: int) -> HttpResponse:
    concert = get_object_or_404(Concert, pk=pk)
    concert.archived = True
    concert.save(update_fields=["archived", "updated_at"])
    return redirect("list")


@require_POST
@login_required
def concert_unarchive(request: HttpRequest, pk: int) -> HttpResponse:
    concert = get_object_or_404(Concert, pk=pk)
    concert.archived = False
    concert.save(update_fields=["archived", "updated_at"])
    return redirect("archives")


@require_POST
@login_required
def concert_delete(request: HttpRequest, pk: int) -> HttpResponse:
    concert = get_object_or_404(Concert, pk=pk)
    concert.delete()
    return redirect("list")
