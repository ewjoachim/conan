# Frontend assets: fetch JS deps (htmx, ...) via npm so they're integrity-checked
# by package-lock.json and tracked by Renovate. Add deps with `npm install <pkg>`.
FROM node:22-slim@sha256:b1e7fcc44bd47f2d186de26c1202345369e7f1028b08956e75cfb52ad8e483f9 AS assets
WORKDIR /assets
COPY package.json package-lock.json ./
RUN npm ci

FROM python:3.14-slim@sha256:44dd04494ee8f3b538294360e7c4b3acb87c8268e4d0a4828a6500b1eff50061

# uv from the official image (no pip middleman).
COPY --from=ghcr.io/astral-sh/uv:0.11.24@sha256:99ea34acedc870ba4ad11a1f540a1c04267c9f30aadc465a94406f52dfda2c36 /uv /uvx /bin/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_FROZEN=1 \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=conan.settings \
    DATABASE_PATH=/data/conan.db

WORKDIR /app

# Install runtime dependencies only (no dev/lint groups) so this layer is cached
# until the lockfile changes and the image stays lean.  BUILD_VERSION is
# forwarded to uv-dynamic-versioning so the package metadata carries the real
# version; CI supplies the tag-derived version, default is 0.0.0.
ARG BUILD_VERSION=0.0.0
COPY pyproject.toml README.md uv.lock ./
# --no-install-project skips building/installing the app itself — only deps —
# so this layer stays valid as long as the lockfile doesn't change.
RUN UV_DYNAMIC_VERSIONING_BYPASS="$BUILD_VERSION" uv sync --no-default-groups --no-install-project

# Vendored JS assets from the npm stage above (not committed to git).
COPY --from=assets /assets/node_modules/htmx.org/dist/htmx.min.js static/conan/htmx.min.js

# Non-root user setup — no application source needed for this.
RUN groupadd -g 10001 app \
    && useradd -u 10001 -g 10001 -m app \
    && mkdir -p /data \
    && chown 10001:10001 /data

# Application source — as late as possible so code changes don't invalidate
# the dependency, vendor-asset and system-setup layers above.
COPY . ./

# Install the project itself (fast, deps are already in the venv).
RUN UV_DYNAMIC_VERSIONING_BYPASS="$BUILD_VERSION" uv sync --no-default-groups

# Collect static assets; WhiteNoise serves them. SECRET_KEY only needs to be
# present, not real, for collectstatic.
RUN SECRET_KEY=build python manage.py collectstatic --noinput

USER 10001:10001

VOLUME /data
EXPOSE 8000

# Liveness probe. A failing check makes `podman auto-update` roll back to the
# previous image (the slim base has no curl, so use Python's stdlib). We connect
# over loopback but send the real Host header (first entry of ALLOWED_HOSTS) so
# production host validation stays strict — no need to allow-list localhost.
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request as u; h=(os.environ.get('ALLOWED_HOSTS') or '127.0.0.1').split(',')[0].strip().lstrip('.') or '127.0.0.1'; u.urlopen(u.Request('http://127.0.0.1:8000/healthz', headers={'Host': h}), timeout=2)"

ENTRYPOINT ["./docker-entrypoint.sh"]
