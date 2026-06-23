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

# htmx is not vendored in git: fetch the pinned version at build time.
ADD https://unpkg.com/htmx.org@2.0.10/dist/htmx.min.js static/conan/htmx.min.js

# Collect static assets; WhiteNoise serves them. SECRET_KEY only needs to be
# present, not real, for collectstatic.
RUN SECRET_KEY=build python manage.py collectstatic --noinput

# Run as a non-root user with fixed ids. /data is the writable volume holding
# the SQLite database; see the README for how the host/quadlet maps ownership.
RUN groupadd -g 10001 app \
    && useradd -u 10001 -g 10001 -m app \
    && mkdir -p /data \
    && chown -R 10001:10001 /app /data \
    && chmod +x docker-entrypoint.sh
USER 10001:10001

VOLUME /data
EXPOSE 8000

ENTRYPOINT ["./docker-entrypoint.sh"]
