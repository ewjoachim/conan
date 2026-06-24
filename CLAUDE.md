# CLAUDE.md

Guidance for working in this repo. See [README.md](README.md) for the stack
overview and dev/run instructions; this file captures the conventions and the
*why* behind decisions that aren't obvious from the code.

## Language

- **UI text is French** (internal tool for a French association).
- **Everything else is English**: code, identifiers, comments, commit messages,
  docs. Don't mix.

## Tooling

- **uv** for deps, **ruff** for lint/format, **ty** for type checking, **prek**
  for hooks. Run everything through `uv run` (e.g. `uv run ruff check`,
  `uv run ty check`, `uv run prek run --all-files`).
- Type checking is **ty**, not mypy/basedpyright. Django's dynamic attributes
  (`.objects`, field descriptors) resolve via the `django-types` package — keep
  it in the lint group.
- The prek config is the **"no versions inside"** style: `builtin` file hooks +
  `local` hooks that shell out to `uv run`. Tool versions live in `uv.lock`,
  not in `.pre-commit-config.yaml`. Don't add pinned `rev:` repos.
- This is a deployed app, not a library: `[tool.uv] package = false`.

## Commits

- **Scoped, conventional commits** (`feat:`, `fix:`, `build:`, `ci:`, `docs:`,
  `chore:`). One concern per commit — if a single file's diff mixes two concerns
  (e.g. a Dockerfile that gains a feature *and* a hardening change), split it
  into separate commits.
- Commit early, commit often.

## Architecture conventions

- **`concerts/checklist.py` is the single source of truth** for the checklist:
  steps, items, item types and progress rules. Change the checklist there, not
  in templates or views.
- **Jinja2 templates** live in `concerts/jinja2/concerts/` (the Jinja backend
  looks in `<app>/jinja2/`, *not* `<app>/templates/`). Files use the
  `.html.jinja` extension.
- **Server-driven HTMX**: each toggle/edit posts a small request; the view
  mutates state and returns the re-rendered fragment plus an out-of-band swap of
  the progress bar. Free-text saves return `204` so the textarea keeps focus.
- **Mutating views** are `@require_POST`, wrap the read-modify-write of
  `Concert.state` in `transaction.atomic()`, and **validate every input against
  the checklist allowlists** (return `400` on anything unknown) — never trust the
  posted key/value blindly. SQLite's `IMMEDIATE` mode + WAL (see settings) makes
  concurrent toggles safe against lost updates.

## Security principles (these came up and matter here)

- **Never weaken a security boundary to paper over an operational
  convenience — fix the operational side instead.** Concrete example from this
  repo: the container healthcheck needed to reach the app, but rather than adding
  `localhost` to `ALLOWED_HOSTS` (which would loosen host validation for *all*
  requests and become a latent cache/redirect-poisoning vector), the probe
  connects over loopback and sends the *real* `Host` header. Keep prod
  `ALLOWED_HOSTS` strict.
- **No secrets in plaintext.** `SECRET_KEY` and friends come from the
  environment; in production they're injected from a secret store, never written
  into a file or committed.
- **Container least privilege**: runs as a non-root fixed UID; `/app` stays
  root-owned and read-only to the runtime user (a compromised process can't
  rewrite its own code); only `/data` (the SQLite volume) is writable.
- **Pin and lock down CI**: digest-pin base images, SHA-pin GitHub Actions, use
  `permissions: {}` at the top level (grant per-job), and
  `persist-credentials: false` on checkout.
- The `/healthz` endpoint is deliberately **no-auth and side-effect-free**; it
  only confirms the app booted and SQLite is reachable. A failing probe drives an
  automatic image rollback, so keep it honest but cheap.

## Frontend assets

- htmx is **not vendored in git**. It's fetched via npm at image build time
  (integrity-checked by `package-lock.json`, Renovate-tracked). For local dev,
  fetch it once (see README).
