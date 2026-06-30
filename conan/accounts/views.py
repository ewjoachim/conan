"""Google Sign-In via Google Identity Services (GIS).

We use the GIS **ID-token** flow, not the OAuth authorization-code flow: the
browser obtains a signed ID token (a JWT) from Google and POSTs it to
``google_callback``. The token-to-user logic lives in
:mod:`conan.accounts.backends`; these views only handle the HTTP shape (parse
the request, run it through ``authenticate``, open or close a Django session).
There is deliberately **no OAuth client secret** anywhere — the ID-token flow is
pure authentication ("who is this user") and does not need one.
"""

import logging

from django.conf import settings
from django.contrib.auth import authenticate, login, logout

# login_not_required exists since Django 5.1 (our floor is 5.2); the django-types
# stubs lag behind, so silence ty's import error here.
from django.contrib.auth.decorators import (
    login_not_required,  # ty: ignore[unresolved-import]
)
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    JsonResponse,
)
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)


@login_not_required
def login_page(request: HttpRequest) -> HttpResponse:
    """Render the "Sign in with Google" page (anonymous-accessible)."""
    if request.user.is_authenticated:
        return redirect("list")
    html = render_to_string(
        "accounts/login.html.jinja",
        {"google_client_id": settings.GOOGLE_OAUTH_CLIENT_ID},
        request,
    )
    response = HttpResponse(html)
    # Google Sign-In opens a popup to accounts.google.com, which sends the
    # credential back via window.opener.postMessage().  Without this header the
    # browser severs the opener reference for cross-origin popups, resulting in
    # "Uncaught TypeError: can't access property 'postMessage', window.opener
    # is null" inside Google's gsi/transform page.
    response["Cross-Origin-Opener-Policy"] = "same-origin-allow-popups"
    return response


@login_not_required
@require_POST
def google_callback(request: HttpRequest) -> HttpResponse:
    """Verify a Google ID token (via the auth backend) and open a session."""
    client_id = settings.GOOGLE_OAUTH_CLIENT_ID
    if not client_id:
        logger.error("GOOGLE_OAUTH_CLIENT_ID is not configured; login is disabled")
        return HttpResponseBadRequest("login not configured")

    credential = request.POST.get("credential", "")
    if not credential:
        return HttpResponseBadRequest("missing credential")

    # GoogleIDTokenBackend does the verification + domain allowlist and logs the
    # specific reason on failure; here we only see authenticated-or-not.
    user = authenticate(request, credential=credential, client_id=client_id)
    if user is None:
        return HttpResponseForbidden("account not allowed")

    login(request, user)
    return JsonResponse({"ok": True})


@require_POST
def logout_view(request: HttpRequest) -> HttpResponse:
    """End the session and bounce back to the login page."""
    logout(request)
    return redirect("login")
