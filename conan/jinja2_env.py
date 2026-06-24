"""Jinja2 environment for Django templates.

Exposes the helpers templates need: static file URLs, named-URL reversing, and
CSRF (both the hidden input for plain forms and the raw token for the HTMX
``hx-headers`` attribute).
"""

from typing import Any, cast

from django.templatetags.static import static
from django.urls import reverse
from jinja2 import Environment

from conan._version import __version__ as conan_version
from conan.concerts import checklist


def environment(**options: Any) -> Environment:
    # The Django Jinja2 backend injects `request`, `csrf_token` and `csrf_input`
    # into the context whenever a request is passed to render, so we don't add
    # CSRF helpers here. It also passes autoescape=True; we set it defensively so
    # the env is safe even if instantiated outside the backend.
    options.setdefault("autoescape", True)
    env = Environment(**options)  # noqa: S701  -- autoescape forced on above
    # env.globals is effectively dict[str, Any] at runtime; the cast keeps the
    # type checker happy about the heterogeneous values we register.
    g = cast("dict[str, Any]", env.globals)
    g["static"] = static
    g["url"] = reverse
    # Checklist rendering helpers, so partials can render any item type.
    g["item_done"] = checklist.item_done
    # App version for the footer.
    g["conan_version"] = conan_version
    g["is_step_done"] = checklist.is_step_done
    g["is_cotech_done"] = checklist.is_cotech_done
    g["COTECH_OPTIONS"] = checklist.COTECH_OPTIONS
    return env
