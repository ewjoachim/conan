"""Server-driven HTMX views.

Each mutating view performs a read-modify-write of ``Concert.state`` inside a
single ``transaction.atomic()`` block. Combined with SQLite's IMMEDIATE
transaction mode (see settings), writers serialize, so concurrent toggles can't
clobber each other's updates to the shared JSON blob.

Most mutations re-render the affected *step* (``hx-target`` is its container) and
piggy-back an out-of-band swap of the header progress bar. Free-text saves are
silent (HTTP 204) so the user's textarea keeps focus while typing.
"""

from django.db import transaction
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from . import checklist
from .models import Concert

META_FIELDS = frozenset(["name", "date", "respo", "mandataire"])


def concert_list(request: HttpRequest) -> HttpResponse:
    concerts = Concert.objects.all()
    html = render_to_string(
        "concerts/list.html.jinja",
        {"concerts": concerts, "count": concerts.count()},
        request,
    )
    return HttpResponse(html)


@require_POST
def concert_create(request: HttpRequest) -> HttpResponse:
    concert = Concert.objects.create(
        name=request.POST.get("name", "").strip(),
        date=request.POST.get("date", "").strip(),
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
    setattr(concert, field, request.POST.get("value", "").strip())
    concert.save(update_fields=[field, "updated_at"])

    if field == "name":
        html = render_to_string(
            "concerts/partials/title.html.jinja",
            {"concert": concert, "oob": True},
            request,
        )
        return HttpResponse(html)
    return HttpResponse(status=204)
