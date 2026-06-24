# CONAN

Internal tool for the Negitachi association to track concert preparation through
a structured checklist. One page lists the concerts; each concert has a
checklist whose progress is saved as you go.

The UI is in French; the code, comments and this documentation are in English.

## Stack

- **Django** (sync) + **Jinja2** templates
- **HTMX** for server-driven interactivity (each toggle/edit posts a small
  request; the server re-renders the affected fragment)
- **SQLite** storage; checklist state is a JSON blob on the `Concert` model
- **Granian** (WSGI) as the application server
- **WhiteNoise** to serve static assets
- **uv** for dependency management, **ruff** for lint/format, **ty** for type
  checking, **prek** to run the hooks

The checklist structure lives in [`concerts/checklist.py`](concerts/checklist.py)
— edit that one module to change steps, items or progress rules.

## Development

```bash
uv sync                       # create the virtualenv from uv.lock
uv run manage.py migrate      # create ./data/conan.db

# htmx is downloaded at build time in Docker; for local dev fetch it once:
curl -fsSL https://unpkg.com/htmx.org@2.0.10/dist/htmx.min.js -o static/conan/htmx.min.js

DEBUG=1 uv run manage.py runserver
# or, to run the production server locally:
DEBUG=1 uv run granian --interface wsgi --host 127.0.0.1 --port 8000 conan.wsgi:application
```

Run the checks before committing:

```bash
uv run ruff check . && uv run ruff format --check .
uv run ty check
uv run prek run --all-files
```

### Configuration

Settings are read from the environment (via `django-environ`):

| Variable | Default | Notes |
|---|---|---|
| `SECRET_KEY` | dev fallback when `DEBUG=1` | **required in production** |
| `DEBUG` | `False` | |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | comma-separated |
| `CSRF_TRUSTED_ORIGINS` | empty | comma-separated, e.g. `https://conan.negitachi.fr` |
| `GOOGLE_OAUTH_CLIENT_ID` | empty | OAuth **client ID** for Sign in with Google (no secret — see below) |
| `GOOGLE_ALLOWED_DOMAIN` | `negitachi.fr` | only verified addresses on this domain may sign in |
| `DATABASE_PATH` | `./data/conan.db` (dev) | set to `/data/conan.db` in the container |
| `TZ` | `Europe/Paris` | |

### Authentication

Every page requires login except `/healthz`. Sign-in uses **Google Identity
Services (the ID-token flow)**: the "Sign in with Google" button hands the
browser a signed ID token (a JWT), which is POSTed to `/auth/google/`; the server
verifies it (signature, **audience = our client ID**, issuer, expiry) with
**PyJWT** and starts a normal Django session. This flow is pure authentication,
so there is **no OAuth client secret** to store anywhere — only the public
`GOOGLE_OAUTH_CLIENT_ID`.

Verifying a token only proves *which* Google account it is, not that the account
belongs here, so access is restricted to one Workspace domain via
`GOOGLE_ALLOWED_DOMAIN` (default `negitachi.fr`): only a Google-*verified* address
on that domain may sign in. With the domain unset the app **fails closed in
production** (nobody can sign in) and, only when `DEBUG=1`, admits any verified
Google account for local convenience. Users are keyed on Google's stable `sub`,
never the mutable email.

#### Getting `GOOGLE_OAUTH_CLIENT_ID`

The client ID is required; without it the login page shows "not configured". To
create one (no billing or app verification needed for an internal tool):

1. In the [Google Cloud Console](https://console.cloud.google.com/), pick or
   create a project.
2. **APIs & Services → OAuth consent screen**: set User type to *Internal* if the
   domain is a Workspace org (only members can then sign in), otherwise *External*.
   Fill in the app name and support email.
3. **APIs & Services → Credentials → Create credentials → OAuth client ID**, with
   application type **Web application**.
4. Under **Authorized JavaScript origins**, add each origin the button loads from
   — `https://conan.negitachi.fr` for prod and `http://localhost:8000` for local
   dev. Leave **Authorized redirect URIs** empty: the ID-token flow doesn't use a
   redirect.
5. Create it and copy the **Client ID** (it ends in `.apps.googleusercontent.com`).
   That value is `GOOGLE_OAUTH_CLIENT_ID`. Ignore the client *secret* — this flow
   never uses it.

## Docker image

The image is built and pushed to `ghcr.io` by
[`.github/workflows/release.yml`](.github/workflows/release.yml) on release.
To build locally:

```bash
docker build -t conan:latest .
```

The container runs as the non-root user `10001:10001`, listens on **port 8000**,
runs migrations on startup, and stores the database under **`/data`** (declared
as a volume). htmx is fetched at build time, so nothing is vendored in git.

A `HEALTHCHECK` probes `/healthz` — a no-auth liveness endpoint that confirms the
app booted and SQLite is reachable. The probe connects over loopback but sends
the real `Host` header (taken from `ALLOWED_HOSTS`), so production host
validation stays strict. Under Podman `AutoUpdate=registry`, a failing probe on a
freshly pulled image rolls back to the previous one.

## Example deployment using Podman Quadlet, rootful, via Ansible

Here's an example with **rootful Podman** (root runs a system quadlet). The database
lives on a **host bind mount** so it can be backed up directly.

The writable-volume trick: under rootful Podman there is no UID remapping — the
container UID maps 1:1 to the host UID. So set the container user to the host
user that should own the files (e.g. `www-data`, UID 33), and `chown` the host
directory to that same UID. No `keep-id` (that is rootless-only).

Let's avoid writing the `SECRET_KEY` in plaintext into the quadlet unit
file (it would land readable on disk on the server). Inject it as a **Podman
secret** mounted into the container's environment; keep the value itself in an
encrypted store (e.g. Ansible Vault), never in the playbook.

Example Ansible task — adapt the host path, port and UID to your setup; this is
illustrative, not copy-paste-perfect:

```yaml
- name: Create CONAN data dir
  ansible.builtin.file:
    path: /srv/conan/data
    state: directory
    owner: "33"          # www-data; must match the container `user` below
    group: "33"
    mode: "0750"

# conan_secret_key comes from an encrypted store (Ansible Vault), not the playbook.
- name: Store CONAN secret key in the Podman secret store
  containers.podman.podman_secret:
    name: conan_secret_key
    state: present
    data: "{{ conan_secret_key }}"

- name: Deploy CONAN quadlet
  containers.podman.podman_container:
    name: conan
    state: quadlet
    image: ghcr.io/ewjoachim/conan:latest
    user: "33:33"                  # rootful: container uid == host uid
    env:
      TZ: Europe/Paris
      ALLOWED_HOSTS: conan.negitachi.fr
      CSRF_TRUSTED_ORIGINS: https://conan.negitachi.fr
      DATABASE_PATH: /data/conan.db
    secrets:
      # Mounts the secret as $SECRET_KEY in the container — never on disk in plaintext.
      - "conan_secret_key,type=env,target=SECRET_KEY"
    publish:
      - "127.0.0.1:8080:8000"      # host:container — proxy 8080 to conan.negitachi.fr
    volume:
      - "/srv/conan/data:/data"    # bind mount → back this path up
    quadlet_options:
      - |
        [Service]
        Restart=always
        RestartSec=5s
```

Then reload and start:

```bash
systemctl daemon-reload
systemctl start conan
```

Proxy `https://conan.negitachi.fr` to `127.0.0.1:8080`.

**Continuous delivery.** The quadlet sets `AutoUpdate=registry` + `Pull=newer`,
so `podman-auto-update.timer` pulls a newly pushed `:latest` and restarts the
container — no deploy step reaches into the server. The timer ships with a daily
schedule; the role tightens it to every ~15 min via a drop-in. Combined with the
image's healthcheck, a broken release is pulled, fails its probe, and is rolled
back automatically.

> If you ever move to **rootless** Podman (running the service as a specific
> user), drop the `user:` line and instead map the in-container user to the host
> user with `UserNS=keep-id:uid=10001,gid=10001`, owning the bind-mount dir with
> that user.
