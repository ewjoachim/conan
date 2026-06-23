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
    PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=conan.settings \
    DATABASE_PATH=/data/conan.db

WORKDIR /app

# Install runtime dependencies only (no dev/lint groups) so this layer is cached
# until the lockfile changes and the image stays lean.
COPY pyproject.toml uv.lock ./
RUN uv sync --no-default-groups --locked

# Application source.
COPY . .

# Vendored JS assets from the npm stage above (not committed to git).
COPY --from=assets /assets/node_modules/htmx.org/dist/htmx.min.js static/conan/htmx.min.js

# Collect static assets; WhiteNoise serves them. SECRET_KEY only needs to be
# present, not real, for collectstatic.
RUN SECRET_KEY=build python manage.py collectstatic --noinput

# Run as a non-root user with fixed ids. /app stays root-owned and is only
# world-readable, so the runtime user can read code/venv/static but cannot
# modify them. Only /data — the SQLite volume — is writable by the app; see the
# README for how the host/quadlet maps ownership.
RUN groupadd -g 10001 app \
    && useradd -u 10001 -g 10001 -m app \
    && mkdir -p /data \
    && chown 10001:10001 /data \
    && chmod +x docker-entrypoint.sh
USER 10001:10001

VOLUME /data
EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
