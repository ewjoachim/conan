"""Django settings for CONAN.

Configuration is read from the environment via django-environ. In production,
values like SECRET_KEY / ALLOWED_HOSTS / CSRF_TRUSTED_ORIGINS are injected by the
quadlet; locally, sensible dev defaults apply.
"""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    CSRF_TRUSTED_ORIGINS=(list, []),
    # "Sign in with Google" (GIS ID-token flow): only the public client id is
    # needed — there is no OAuth client *secret* in this flow. GOOGLE_ALLOWED
    # is a comma-separated list of entries: `@domain.tld` admits the whole
    # domain; `user@domain.tld` admits one address. An empty list fails closed
    # in production.
    GOOGLE_OAUTH_CLIENT_ID=(str, ""),
    GOOGLE_ALLOWED=(list, ["@negitachi.fr"]),
    # In prod the DB lives on the mounted volume at /data; dev defaults to ./data.
    DATABASE_PATH=(str, str(BASE_DIR / "data" / "conan.db")),
)

DEBUG = env("DEBUG")

# Dev-only fallback secret; production must provide SECRET_KEY via the environment.
SECRET_KEY = env("SECRET_KEY", default="dev-insecure-key-change-me" if DEBUG else "")

ALLOWED_HOSTS = env("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")

# Google Sign-In (see accounts.views for the flow and security notes).
GOOGLE_OAUTH_CLIENT_ID = env("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_ALLOWED = env("GOOGLE_ALLOWED")

# Anonymous users hitting a login-required view are redirected here.
LOGIN_URL = "login"

# Sign-in is Google-only — there are no password accounts and no Django admin, so
# the default ModelBackend is dropped entirely. In DEBUG we prepend a dev backend
# that logs you in as a `root` superuser (driven by DevAutoLoginMiddleware below),
# so local work never has to round-trip through Google.
AUTHENTICATION_BACKENDS = ["conan.accounts.backends.GoogleIDTokenBackend"]
if DEBUG:
    AUTHENTICATION_BACKENDS.insert(0, "conan.accounts.backends.DevAutoLoginBackend")

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "conan.accounts",
    "conan.concerts",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    # Require auth for *every* view by default; opt out with @login_not_required
    # (healthz, the login page, the Google callback). Fail closed: a new view is
    # protected unless it explicitly says otherwise.
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# DEBUG only: auto-login as `root`. Must sit *after* AuthenticationMiddleware
# (request.user must exist) and *before* LoginRequiredMiddleware (the session
# must be authenticated before the login gate runs).
if DEBUG:
    MIDDLEWARE.insert(
        MIDDLEWARE.index("django.contrib.auth.middleware.LoginRequiredMiddleware"),
        "conan.accounts.middleware.DevAutoLoginMiddleware",
    )

ROOT_URLCONF = "conan.urls"
WSGI_APPLICATION = "conan.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        # Project-level shared templates (e.g. the base layout) live here, so they
        # don't belong to any single app; per-app templates use APP_DIRS below.
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "environment": "conan.jinja2_env.environment",
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": env("DATABASE_PATH"),
        "OPTIONS": {
            # IMMEDIATE makes transaction.atomic() grab the write lock up front,
            # so concurrent toggles serialize cleanly instead of risking lost
            # updates on the JSON state blob. WAL + busy_timeout let a second
            # writer wait briefly rather than erroring.
            "transaction_mode": "IMMEDIATE",
            "init_command": "PRAGMA journal_mode=WAL; PRAGMA busy_timeout=5000;",
        },
    },
}

LANGUAGE_CODE = "fr"
TIME_ZONE = env("TZ", default="Europe/Paris")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
