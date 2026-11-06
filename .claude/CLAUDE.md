# kelseys-site

Multi-site project hosting several `*.kelseys.site` subdomains on a shared DigitalOcean
droplet. As of the 2026-11 restructure, this is **one monorepo** (`mr-kelsey/kelseys-site`)
with one top-level directory per subdomain, each deployed independently via a path-filtered
GitHub Actions workflow — not, as before, a separate git repo per subdomain.

## Layout

- `mr/` — Mr. Kelsey's resume/portfolio site (live at mr.kelseys.site). Fully built. See
  `mr/.claude/CLAUDE.md` for its stack decisions, deploy pipeline, and content model. Don't
  re-litigate decisions documented there without asking.
- `mrs/` — Mrs. Kelsey's formulation-company site (brand: Kaleidoscopic Creations), live at
  mrs.kelseys.site. See `mrs/.claude/CLAUDE.md` (naming/deploy facts) and
  `mrs/.claude/NEXT_STEPS.md` (current open work).
- `root/` — the bare `kelseys.site` domain: public recipe book + admin-only family calendar.
  `root/has-calendar` is a symlink to an unrelated-looking standalone project, gitignored,
  reference-only — the calendar logic was ported from it, not imported from it.
- `proxy-serve/` — shared reverse-proxy/TLS infra (Caddy), joined to every subdomain's `app`
  container via the external `shared-web` Docker network.

Each directory's own `.claude/CLAUDE.md` governs the specifics of that site only. This file,
plus the user's global `~/.claude/` rules (TDD, no wildcard imports, OOP where it fits, no
`global` keyword, descriptive names), govern work across this whole project.

## Working in this repo: sparse-checkout

This repo is meant to grow to 15-20 subdomains. Don't clone the whole thing and work with
everything materialized — use sparse-checkout to keep your working tree scoped to whatever
you're actually touching:

```bash
git clone --no-checkout https://github.com/mr-kelsey/kelseys-site.git
cd kelseys-site
git sparse-checkout init --cone
git sparse-checkout set root mr      # whichever subdomain(s) you're working on
git checkout main
```

Add or drop folders later without re-cloning: `git sparse-checkout add mrs`,
`git sparse-checkout set root` (replaces the whole set), `git sparse-checkout disable` (back
to everything).

## Cross-site conventions

- Each Python site manages its own `.venv` independently (`cd mr && uv sync`, etc.) — there
  is no shared venv at the repo root, and there shouldn't be: the repo root has no
  `pyproject.toml` of its own, and sites' dependencies genuinely diverge (`mrs` needs
  `resend`, others don't; this only gets more true as more sites are added). A root-level
  `.venv` also can't hold two sites' dependencies installed at once, which defeats a chunk of
  the point of working across sites in one session. Every site's `.gitignore`-driven tooling
  (CI's `working-directory: ${{ inputs.site_dir }}` + `.venv/bin/pytest`, Docker's own
  `uv sync` inside each build context) assumes this.
- Each site gets its own `deploy-{name}` SSH user on the droplet, forced-command-restricted
  to only that site's `/opt/{name}/deploy.sh` — a leaked key for one site can't touch
  another's. Unchanged by the monorepo move: `/opt/{name}` is now a sparse-checkout clone of
  this one repo scoped to `{name}/`, rather than a clone of a dedicated repo.
- Each site joins `shared-web` under an explicit, unique container name (not the bare Compose
  service name `app`, which collides across projects on a shared network).
- **Deploys**: one reusable workflow (`.github/workflows/deploy-reusable.yml`) holds the
  test-then-SSH-deploy job body. Each site has a thin trigger workflow
  (`.github/workflows/deploy-{name}.yml`) that fires only on pushes to `main` touching
  `{name}/**`, and calls the reusable workflow with that site's `site_dir` and credentials.
  Credentials are repo secrets prefixed per site (`MR_SSH_USER`/`MR_SSH_PRIVATE_KEY`,
  `MRS_SSH_USER`/`MRS_SSH_PRIVATE_KEY`, etc.) — `SSH_HOST` is shared (one droplet for every
  site). The deploy step itself is always `script: echo "deploying"`; that's intentional, not
  a gap — see the forced-command note above. Don't "fix" it.

### Adding a new subdomain

1. New top-level directory, built like any of the existing sites.
2. Copy an existing thin trigger workflow (e.g. `deploy-root.yml`) to
   `deploy-{name}.yml`, swap `site_dir` and the two secret names.
3. Add the `{NAME}_SSH_USER` / `{NAME}_SSH_PRIVATE_KEY` repo secrets (GitHub web UI).
4. Provision a `deploy-{name}` droplet user + forced-command-restricted key, same as every
   other site.
5. Add the Caddyfile block in `proxy-serve/` and redeploy it.

No changes to `deploy-reusable.yml` needed — it's already generic across every Python/uv
site; a non-Python site overrides `test_command` (see `deploy-proxy-serve.yml` for the
pattern, which validates a Caddyfile instead of running pytest).

## History note

This repo was assembled 2026-11-05 from three previously-separate repos
(`mr-kelsey/personal-webpage`, `mr-kelsey/mrs-kelsey-personal-webpage`,
`mr-kelsey/caddy-infra-personal-website`) via `git subtree`, preserving each one's full commit
history under its new directory prefix — not squashed. `mr/single-site-fasthtml-base` is a
real branch carried over from the old `mr.` repo; note that because that branch predates the
monorepo split, checking it out shows the old repo's tree at the branch's root (no `mr/`
prefix) rather than today's monorepo layout — it's a historical snapshot, not something to
build on directly. The old standalone repos are kept (not deleted) as a rollback path until
the monorepo deploy is verified for every site, then get archived.
