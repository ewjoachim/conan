import datetime
from typing import Any

from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from . import checklist_orga as checklist
from .models import OrgaConcert

META_FIELDS = frozenset(["name", "date", "lieu", "respo", "contact_salle"])
VISIBILITY_ITEMS = frozenset(["sg_collab", "sg_scenario"])


@require_POST
def orga_create(request: HttpRequest) -> HttpResponse:
    raw_date = request.POST.get("date", "").strip()
    try:
        parsed_date = datetime.date.fromisoformat(raw_date) if raw_date else None
    except ValueError:
        parsed_date = None
    concert = OrgaConcert.objects.create(
        name=request.POST.get("name", "").strip(),
        date=parsed_date,
        respo=request.POST.get("respo", "").strip(),
    )
    return redirect("o_detail", pk=concert.pk)


def orga_detail(request: HttpRequest, pk: int) -> HttpResponse:
    concert = get_object_or_404(OrgaConcert, pk=pk)
    html = render_to_string(
        "concerts_orga/detail.html.jinja",
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
    request: HttpRequest, concert: OrgaConcert, step: checklist.Step
) -> str:
    context = {
        "concert": concert,
        "step": step,
        "state": concert.state,
        "open_step_id": step.id,
    }
    step_html = render_to_string(
        "concerts_orga/partials/step.html.jinja", context, request
    )
    progress_html = render_to_string(
        "concerts_orga/partials/progress.html.jinja",
        {"progress": checklist.compute_progress(concert.state), "oob": True},
        request,
    )
    return step_html + progress_html


def _render_step(
    request: HttpRequest, concert: OrgaConcert, step_id: str
) -> HttpResponse:
    step = checklist.STEPS_BY_ID[step_id]
    return HttpResponse(_render_step_and_progress(request, concert, step))


@require_POST
def orga_toggle(request: HttpRequest, pk: int) -> HttpResponse:
    key = request.POST.get("key", "")
    step_id = request.POST.get("step", "")
    if key not in checklist.TOGGLE_KEYS or step_id not in checklist.STEPS_BY_ID:
        return HttpResponseBadRequest("unknown key or step")
    with transaction.atomic():
        concert = get_object_or_404(OrgaConcert, pk=pk)
        concert.state[key] = not concert.state.get(key, False)
        concert.progress = checklist.compute_progress(concert.state).pct
        concert.save(update_fields=["state", "progress", "updated_at"])
    return _render_step(request, concert, step_id)


@require_POST
def orga_yesno(request: HttpRequest, pk: int) -> HttpResponse:
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
        concert = get_object_or_404(OrgaConcert, pk=pk)
        concert.state[f"yn_{item_id}"] = val
        concert.progress = checklist.compute_progress(concert.state).pct
        concert.save(update_fields=["state", "progress", "updated_at"])

    if item_id in VISIBILITY_ITEMS:
        all_steps_html = render_to_string(
            "concerts_orga/partials/all_steps.html.jinja",
            {
                "steps": checklist.STEPS,
                "state": concert.state,
                "concert": concert,
                "open_step_id": step_id,
            },
            request,
        )
        progress_html = render_to_string(
            "concerts_orga/partials/progress.html.jinja",
            {"progress": checklist.compute_progress(concert.state), "oob": True},
            request,
        )
        return HttpResponse(all_steps_html + progress_html)

    return _render_step(request, concert, step_id)


@require_POST
def orga_cotech_mode(request: HttpRequest, pk: int) -> HttpResponse:
    mode = request.POST.get("mode", "")
    step_id = request.POST.get("step", "")
    if mode not in checklist.COTECH_MODES or step_id not in checklist.STEPS_BY_ID:
        return HttpResponseBadRequest("invalid cotech mode")
    with transaction.atomic():
        concert = get_object_or_404(OrgaConcert, pk=pk)
        concert.state["cotech_mode"] = mode
        concert.progress = checklist.compute_progress(concert.state).pct
        concert.save(update_fields=["state", "progress", "updated_at"])
    return _render_step(request, concert, step_id)


@require_POST
def orga_field(request: HttpRequest, pk: int) -> HttpResponse:
    key = request.POST.get("key", "")
    if key not in checklist.TEXT_KEYS:
        return HttpResponseBadRequest("unknown field")
    with transaction.atomic():
        concert = get_object_or_404(OrgaConcert, pk=pk)
        concert.state[key] = request.POST.get("text", "")
        concert.save(update_fields=["state", "updated_at"])
    return HttpResponse(status=204)


@require_POST
def orga_meta(request: HttpRequest, pk: int) -> HttpResponse:
    field = request.POST.get("field", "")
    if field not in META_FIELDS:
        return HttpResponseBadRequest("unknown field")
    concert = get_object_or_404(OrgaConcert, pk=pk)
    value: Any = request.POST.get("value", "").strip()
    if field == "date":
        value = datetime.date.fromisoformat(value) if value else None
    setattr(concert, field, value)
    concert.save(update_fields=[field, "updated_at"])
    if field == "name":
        html = render_to_string(
            "concerts_orga/partials/title.html.jinja",
            {"concert": concert, "oob": True},
            request,
        )
        return HttpResponse(html)
    return HttpResponse(status=204)


@require_POST
def collab_add(request: HttpRequest, pk: int) -> HttpResponse:
    step_id = request.POST.get("step", "")
    if step_id not in checklist.STEPS_BY_ID:
        return HttpResponseBadRequest("unknown step")
    with transaction.atomic():
        concert = get_object_or_404(OrgaConcert, pk=pk)
        collabs: list[dict[str, object]] = list(concert.state.get("o_collabs", []))
        collabs.append({"nom": "", "nb_chantants": "", "nb_non_chantants": ""})
        concert.state["o_collabs"] = collabs
        concert.save(update_fields=["state", "updated_at"])
    return _render_step(request, concert, step_id)


@require_POST
def collab_delete(request: HttpRequest, pk: int, idx: int) -> HttpResponse:
    step_id = request.POST.get("step", "")
    if step_id not in checklist.STEPS_BY_ID:
        return HttpResponseBadRequest("unknown step")
    with transaction.atomic():
        concert = get_object_or_404(OrgaConcert, pk=pk)
        collabs = list(concert.state.get("o_collabs", []))
        if 0 <= idx < len(collabs):
            collabs.pop(idx)
        concert.state["o_collabs"] = collabs
        concert.save(update_fields=["state", "updated_at"])
    return _render_step(request, concert, step_id)


@require_POST
def collab_update(request: HttpRequest, pk: int, idx: int) -> HttpResponse:
    with transaction.atomic():
        concert = get_object_or_404(OrgaConcert, pk=pk)
        collabs = list(concert.state.get("o_collabs", []))
        if 0 <= idx < len(collabs):
            collab = dict(collabs[idx])
            for f in ("nom", "nb_chantants", "nb_non_chantants"):
                if f in request.POST:
                    collab[f] = request.POST[f].strip()
            collabs[idx] = collab
        concert.state["o_collabs"] = collabs
        concert.save(update_fields=["state", "updated_at"])
    return HttpResponse(status=204)


@require_POST
def intervenant_add(request: HttpRequest, pk: int) -> HttpResponse:
    step_id = request.POST.get("step", "")
    if step_id not in checklist.STEPS_BY_ID:
        return HttpResponseBadRequest("unknown step")
    with transaction.atomic():
        concert = get_object_or_404(OrgaConcert, pk=pk)
        intervenants: list[dict[str, object]] = list(
            concert.state.get("o_intervenants", [])
        )
        intervenants.append({"nom": "", "contact": ""})
        concert.state["o_intervenants"] = intervenants
        concert.save(update_fields=["state", "updated_at"])
    return _render_step(request, concert, step_id)


@require_POST
def intervenant_delete(request: HttpRequest, pk: int, idx: int) -> HttpResponse:
    step_id = request.POST.get("step", "")
    if step_id not in checklist.STEPS_BY_ID:
        return HttpResponseBadRequest("unknown step")
    with transaction.atomic():
        concert = get_object_or_404(OrgaConcert, pk=pk)
        intervenants = list(concert.state.get("o_intervenants", []))
        if 0 <= idx < len(intervenants):
            intervenants.pop(idx)
        concert.state["o_intervenants"] = intervenants
        concert.save(update_fields=["state", "updated_at"])
    return _render_step(request, concert, step_id)


@require_POST
def intervenant_update(request: HttpRequest, pk: int, idx: int) -> HttpResponse:
    with transaction.atomic():
        concert = get_object_or_404(OrgaConcert, pk=pk)
        intervenants = list(concert.state.get("o_intervenants", []))
        if 0 <= idx < len(intervenants):
            interv = dict(intervenants[idx])
            for f in ("nom", "contact"):
                if f in request.POST:
                    interv[f] = request.POST[f].strip()
            intervenants[idx] = interv
        concert.state["o_intervenants"] = intervenants
        concert.save(update_fields=["state", "updated_at"])
    return HttpResponse(status=204)


@require_POST
def orepet_add(request: HttpRequest, pk: int) -> HttpResponse:
    step_id = request.POST.get("step", "")
    if step_id not in checklist.STEPS_BY_ID:
        return HttpResponseBadRequest("unknown step")
    with transaction.atomic():
        concert = get_object_or_404(OrgaConcert, pk=pk)
        repets: list[dict[str, str | None]] = list(concert.state.get("o_repets", []))
        repets.append({"date": None, "lieu": ""})
        concert.state["o_repets"] = repets
        concert.save(update_fields=["state", "updated_at"])
    return _render_step(request, concert, step_id)


@require_POST
def orepet_delete(request: HttpRequest, pk: int, idx: int) -> HttpResponse:
    step_id = request.POST.get("step", "")
    if step_id not in checklist.STEPS_BY_ID:
        return HttpResponseBadRequest("unknown step")
    with transaction.atomic():
        concert = get_object_or_404(OrgaConcert, pk=pk)
        repets = list(concert.state.get("o_repets", []))
        if 0 <= idx < len(repets):
            repets.pop(idx)
        concert.state["o_repets"] = repets
        concert.save(update_fields=["state", "updated_at"])
    return _render_step(request, concert, step_id)


@require_POST
def orepet_update(request: HttpRequest, pk: int, idx: int) -> HttpResponse:
    with transaction.atomic():
        concert = get_object_or_404(OrgaConcert, pk=pk)
        repets = list(concert.state.get("o_repets", []))
        if 0 <= idx < len(repets):
            repet = dict(repets[idx])
            if "date" in request.POST:
                repet["date"] = request.POST["date"].strip() or None
            if "lieu" in request.POST:
                repet["lieu"] = request.POST["lieu"].strip()
            repets[idx] = repet
        concert.state["o_repets"] = repets
        concert.save(update_fields=["state", "updated_at"])
    return HttpResponse(status=204)


@require_POST
def extra_add(request: HttpRequest, pk: int) -> HttpResponse:
    step_id = request.POST.get("step", "")
    if step_id not in checklist.STEPS_BY_ID:
        return HttpResponseBadRequest("unknown step")
    with transaction.atomic():
        concert = get_object_or_404(OrgaConcert, pk=pk)
        extras: list[dict[str, object]] = list(concert.state.get("extras", []))
        extras.append({"desc": "", "done": False})
        concert.state["extras"] = extras
        concert.save(update_fields=["state", "updated_at"])
    return _render_step(request, concert, step_id)


@require_POST
def extra_delete(request: HttpRequest, pk: int, idx: int) -> HttpResponse:
    step_id = request.POST.get("step", "")
    if step_id not in checklist.STEPS_BY_ID:
        return HttpResponseBadRequest("unknown step")
    with transaction.atomic():
        concert = get_object_or_404(OrgaConcert, pk=pk)
        extras = list(concert.state.get("extras", []))
        if 0 <= idx < len(extras):
            extras.pop(idx)
        concert.state["extras"] = extras
        concert.save(update_fields=["state", "updated_at"])
    return _render_step(request, concert, step_id)


@require_POST
def extra_update(request: HttpRequest, pk: int, idx: int) -> HttpResponse:
    with transaction.atomic():
        concert = get_object_or_404(OrgaConcert, pk=pk)
        extras = list(concert.state.get("extras", []))
        if 0 <= idx < len(extras):
            extra = dict(extras[idx])
            extra["desc"] = request.POST.get("desc", "").strip()
            extras[idx] = extra
        concert.state["extras"] = extras
        concert.save(update_fields=["state", "updated_at"])
    return HttpResponse(status=204)


@require_POST
def extra_toggle(request: HttpRequest, pk: int, idx: int) -> HttpResponse:
    step_id = request.POST.get("step", "")
    if step_id not in checklist.STEPS_BY_ID:
        return HttpResponseBadRequest("unknown step")
    with transaction.atomic():
        concert = get_object_or_404(OrgaConcert, pk=pk)
        extras = list(concert.state.get("extras", []))
        if 0 <= idx < len(extras):
            extra = dict(extras[idx])
            extra["done"] = not extra.get("done")
            extras[idx] = extra
        concert.state["extras"] = extras
        concert.save(update_fields=["state", "updated_at"])
    return _render_step(request, concert, step_id)


@require_POST
@login_required
def orga_archive(request: HttpRequest, pk: int) -> HttpResponse:
    concert = get_object_or_404(OrgaConcert, pk=pk)
    concert.archived = True
    concert.save(update_fields=["archived", "updated_at"])
    return redirect("list")


@require_POST
@login_required
def orga_unarchive(request: HttpRequest, pk: int) -> HttpResponse:
    concert = get_object_or_404(OrgaConcert, pk=pk)
    concert.archived = False
    concert.save(update_fields=["archived", "updated_at"])
    return redirect("archives")


@require_POST
@login_required
def orga_delete(request: HttpRequest, pk: int) -> HttpResponse:
    concert = get_object_or_404(OrgaConcert, pk=pk)
    concert.delete()
    return redirect("list")
