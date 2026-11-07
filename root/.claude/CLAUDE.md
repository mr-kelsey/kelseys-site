# kelseys.site (recipe book + family calendar)

The bare `kelseys.site` domain: a public recipe book (filterable by name/ingredient/servings,
trie-backed live-narrowing search, a "random recipe" draw with ingredient exclusion/re-roll)
plus an admin-only family calendar. Shared-password auth, same single-owner simplification as
`mr`/`mrs`. See `README.md` for the project structure, local dev, and test commands. This
directory is one of several `*.kelseys.site` subdomains in the `kelseys-site` monorepo — see
the repo-root `.claude/CLAUDE.md` for the overall layout and shared-infra conventions.

- Added to the monorepo with no prior standalone-repo history (unlike `mr`/`mrs`, which were
  `git subtree`-merged in from their own old repos) — see the repo-root CLAUDE.md's "History
  note".
- Naming: `pyproject.toml` name `kelseys-root`; Docker `container_name` `kelseys-root-app`;
  droplet deploy user `deploy-root`; `/opt` path `/opt/kelseys-root` — a legacy-style name
  chosen to match the pattern of `mr`/`mrs`'s pre-monorepo basenames even though `root` never
  had one of its own; there's no volume-naming constraint forcing this choice the way there
  was for `mr`/`mrs`. Deployed by `.github/workflows/deploy-root.yml` (path-filtered on
  `root/**`), credentials in `ROOT_SSH_USER`/`ROOT_SSH_PRIVATE_KEY` repo secrets.
- Droplet-side provisioning (the `deploy-root` user, its forced-command SSH key, and the
  `/opt/kelseys-root` sparse-checkout clone) was done via
  `.claude/resources/provision-subdomain.sh` (repo-root, gitignored, local-only) rather than by
  hand — that script is the reusable path for provisioning any future subdomain too.
- `docker-compose.yml` bind-mounts `./family.json:/app/family.json:ro` — real family member
  names/colors, gitignored, never committed. **This must be placed on the droplet by hand
  before the first deploy** (`cp family.example.json family.json`, fill in real values) — it's
  real personal content, not something a provisioning script should invent. Missing it isn't
  harmless: Docker's bind-mount auto-create silently makes an empty *directory* at that host
  path when the source is missing, which crashes the app at startup trying to open it as a
  file, and — because a container's mount spec is fixed at creation time, not re-evaluated
  unless `docker compose up` recreates it — fixing the host file afterward isn't enough on its
  own; the existing container also needs recreating (`docker compose up -d --force-recreate`,
  which `deploy.sh` always passes, precisely because of this).
- Deployment: **live**, fully wired and verified end-to-end 2026-11-07 (`deploy-root.yml` green,
  `kelseys.site` block in `proxy-serve/Caddyfile` reverse-proxying to `kelseys-root-app:8080`,
  DNS apex resolving, deploy-proxy-serve.yml health-checking it successfully). `deploy.sh`'s own
  health check runs *inside* the container against its own `localhost:8080/healthz`, not the
  public URL through Caddy — this site's deploy and `proxy-serve`'s Caddyfile deploy have no
  ordering requirement against each other as a result. Same caveat as every other site: pushing
  to `main` ships a release — confirm before pushing.
- The droplet this runs on is memory-constrained (512MB, no swap originally — swap was added
  2026-11-07 specifically because a `docker compose build` memory spike froze the box). Keep an
  eye on this if/when more subdomains are added; a droplet resize may be needed before this
  repo gets anywhere near its planned 15-20 subdomains.
