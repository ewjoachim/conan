"""Google Sign-In via Google Identity Services (GIS).

We use the GIS **ID-token** flow, not the OAuth authorization-code flow: the
browser obtains a signed ID token (a JWT) from Google and POSTs it to
``google_callback``. We verify it server-side and start a normal Django session
with ``django.contrib.auth.login``. There is deliberately **no OAuth client
secret** anywhere — the ID-token flow is pure authentication ("who is this
user") and does not need one. See the README for the full rationale.

Access is gated by a Workspace domain (``GOOGLE_ALLOWED_DOMAIN``): verifying a
Google token only proves *which* Google account it is, not that the account
belongs here, so we fail **closed** in production when no domain is configured.
"""

import logging
from typing import Any

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model, login, logout

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
from jwt import PyJWKClient

logger = logging.getLogger(__name__)
User = get_user_model()

# Google's public signing keys (JWKS) and the two issuer strings it uses. The
# client fetches and caches the keys over stdlib urllib.
_GOOGLE_CERTS_URL = "https://www.googleapis.com/oauth2/v3/certs"
_GOOGLE_ISSUERS = {"https://accounts.google.com", "accounts.google.com"}
_jwks_client = PyJWKClient(_GOOGLE_CERTS_URL)


def _verify_google_token(credential: str, client_id: str) -> dict[str, Any]:
    """Verify a Google ID token and return its claims.

    Validating the ``aud`` (audience) is the whole security boundary: it
    confirms the token was minted for *our* client id. PyJWT also checks the
    RS256 signature against Google's JWKS and the expiry; we assert the issuer
    explicitly to accept either Google issuer string. Raises ``jwt.PyJWTError``
    on any failure (bad signature, wrong audience, expired, unreachable JWKS).
    """
    signing_key = _jwks_client.get_signing_key_from_jwt(credential)
    claims: dict[str, Any] = jwt.decode(
        credential,
        signing_key.key,
        algorithms=["RS256"],
        audience=client_id,
        options={"require": ["exp", "aud", "iss", "sub"]},
    )
    if claims.get("iss") not in _GOOGLE_ISSUERS:
        raise jwt.InvalidIssuerError(claims.get("iss"))
    return claims


def _is_allowed(email: str) -> bool:
    """Whether ``email`` may sign in.

    Sign-in is restricted to a single Workspace domain
    (``GOOGLE_ALLOWED_DOMAIN``, e.g. ``negitachi.fr``). The email is matched on
    its domain part only after Google has marked it verified (checked by the
    caller). With no domain configured we admit any verified Google account in
    DEBUG for local dev, but deny everyone in production — never silently open
    the door.
    """
    domain = settings.GOOGLE_ALLOWED_DOMAIN.strip().lower()
    if not domain:
        return bool(settings.DEBUG)
    return email.lower().endswith(f"@{domain}")


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
    return HttpResponse(html)


@login_not_required
@require_POST
def google_callback(request: HttpRequest) -> HttpResponse:
    """Verify a Google ID token and open a Django session."""
    client_id = settings.GOOGLE_OAUTH_CLIENT_ID
    if not client_id:
        logger.error("GOOGLE_OAUTH_CLIENT_ID is not configured; login is disabled")
        return HttpResponseBadRequest("login not configured")

    credential = request.POST.get("credential", "")
    if not credential:
        return HttpResponseBadRequest("missing credential")

    try:
        claims = _verify_google_token(credential, client_id)
    except jwt.PyJWTError:
        # Bad signature, wrong audience/issuer, expired, malformed, JWKS fetch...
        logger.warning("Google ID token verification failed", exc_info=True)
        return HttpResponseBadRequest("invalid token")

    if not claims.get("email_verified"):
        return HttpResponseForbidden("email not verified")

    email = claims.get("email", "")
    if not _is_allowed(email):
        logger.warning(
            "Rejected Google login for %r (not on the allowed domain)", email
        )
        return HttpResponseForbidden("account not allowed")

    # Key on the stable Google subject id, never the (mutable, reassignable)
    # email — keying on email is a quiet account-takeover vector. Email and name
    # are profile data we refresh on each login.
    user, _ = User.objects.get_or_create(
        username=claims["sub"],
        defaults={
            "email": email,
            "first_name": claims.get("given_name", ""),
            "last_name": claims.get("family_name", ""),
        },
    )
    if user.email != email:
        user.email = email
        user.save(update_fields=["email"])

    login(request, user)
    return JsonResponse({"ok": True})


@require_POST
def logout_view(request: HttpRequest) -> HttpResponse:
    """End the session and bounce back to the login page."""
    logout(request)
    return redirect("login")
