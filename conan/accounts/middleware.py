"""Local-dev auto-login middleware.

Wired into ``MIDDLEWARE`` only when ``DEBUG`` is true (see settings), and
positioned *after* ``AuthenticationMiddleware`` (so ``request.user`` exists) and
*before* ``LoginRequiredMiddleware`` (so the session is already authenticated by
the time the login gate runs). It drives :class:`accounts.backends.DevAutoLoginBackend`,
logging the developer in as ``root`` on the first request so nobody has to click
through Google to work locally.
"""

from collections.abc import Callable

from django.contrib.auth import authenticate, login
from django.http import HttpRequest, HttpResponse


class DevAutoLoginMiddleware:
    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if not request.user.is_authenticated:
            user = authenticate(request, dev_autologin=True)
            if user is not None:
                login(request, user)
        return self.get_response(request)
