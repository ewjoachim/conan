"""Authentication backends for CONAN.

:class:`GoogleIDTokenBackend` turns a verified Google ID token into a Django
user — the "credential → user" half of sign-in lives here, while the HTTP half
(parsing the POST, status codes) stays in ``accounts.views``. It is the only
entry in ``settings.AUTHENTICATION_BACKENDS``; sign-in is Google-only, so the
default ``ModelBackend`` is dropped.

Access is gated by a Workspace domain (``GOOGLE_ALLOWED_DOMAIN``): verifying a
Google token only proves *which* Google account it is, not that the account
belongs here, so we fail **closed** in production when no domain is configured.
"""

import logging
from typing import Any

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import AbstractBaseUser
from django.http import HttpRequest
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


class GoogleIDTokenBackend(BaseBackend):
    """Authenticate a Google Identity Services ID token (the JWT credential).

    ``authenticate`` returns the matching user or ``None``; every failure mode
    (bad token, unverified email, wrong domain) collapses to ``None`` and is
    logged here where the reason is still known. The view only learns
    success/failure, which is all it needs to pick a status code.
    """

    # Backends legitimately take credential-specific kwargs rather than the stub's
    # username/password, so the override signature differs by design.
    def authenticate(  # ty: ignore[invalid-method-override]
        self,
        request: HttpRequest | None,
        credential: str | None = None,
        client_id: str | None = None,
        **kwargs: Any,
    ) -> AbstractBaseUser | None:
        if not credential or not client_id:
            return None

        try:
            claims = _verify_google_token(credential, client_id)
        except jwt.PyJWTError:
            # Bad signature, wrong audience/issuer, expired, malformed, JWKS fetch...
            logger.warning("Google ID token verification failed", exc_info=True)
            return None

        if not claims.get("email_verified"):
            logger.warning("Rejected Google login: email not verified")
            return None

        email = claims.get("email", "")
        if not _is_allowed(email):
            logger.warning(
                "Rejected Google login for %r (not on the allowed domain)", email
            )
            return None

        # Key on the stable Google subject id, never the (mutable, reassignable)
        # email — keying on email is a quiet account-takeover vector. Email and
        # name are profile data we refresh on each login.
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
        return user

    def get_user(self, user_id: int) -> AbstractBaseUser | None:
        return User.objects.filter(pk=user_id).first()
