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
    # In prod the DB lives on the mounted volume at /data; dev defaults to ./data.
    DATABASE_PATH=(str, str(BASE_DIR / "data" / "conan.db")),
)

DEBUG = env("DEBUG")

# Dev-only fallback secret; production must provide SECRET_KEY via the environment.
SECRET_KEY = env("SECRET_KEY", default="dev-insecure-key-change-me" if DEBUG else "")

ALLOWED_HOSTS = env("ALLOWED_HOSTS")
CSRF_TRUSTED_ORIGINS = env("CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "conan.concerts",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

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
