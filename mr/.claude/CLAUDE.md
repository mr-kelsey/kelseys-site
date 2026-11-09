# mr-kelsey

Personal resume/portfolio site for Johnathan Kelsey (BS Cybersecurity, MS Applied AI): resume, portfolio/work, blog, admin, and contact pages. Built with [FastHTML](https://www.fastht.ml/). Live at https://mr.kelseys.site — this is an established, deployed site, not a greenfield build. This directory is one of several `*.kelseys.site` subdomains in the `kelseys-site` monorepo — see the repo-root `.claude/CLAUDE.md` for the overall layout and shared-infra conventions.

## Current stack and key decisions (do not re-litigate without asking)

- Content (Work/Blog/contact messages) in **SQLite via `fastlite`**.
- Hosted on a **DigitalOcean droplet**, shared with other `*.kelseys.site` subdomains. This site's `docker-compose.yml` runs only the FastHTML `app` container (`container_name: mr-kelsey-app`), joined to an external Docker network `shared-web`. TLS/reverse-proxy is **not** here — it's owned by the sibling `proxy-serve/` directory (formerly its own `caddy-infra` repo), which every subdomain's app joins by container name (not bare service name — Compose's service-name DNS alias is scoped per-network, not per-project, and collides once a second site also has a service named `app`).
- Deploys via GitHub Actions (`.github/workflows/deploy-mr.yml` + the shared `deploy-reusable.yml`, path-filtered on `mr/**`): a test gate, then SSH (as `deploy-mr`, a forced-command-restricted key — it can only run the deploy script, even with the private key in hand) to `deploy.sh` on the server, which health-checks `/healthz` and rolls back the image/commit on failure. Each subdomain has its own `deploy-{name}` user scoped to only its own `/opt/{name}` path, so a leaked key for one site can't touch another's.
- Content management (create/edit/delete Work & Blog entries) lives at `/admin` — single shared-password auth, deliberate simplification for a single-owner site (no multi-user, no MFA). No SSH needed for routine content edits.
- Visual style: minimal, whitespace-heavy, typography-led, dark "case file" theme — see the header comment in `static/css/site.css` for the design rationale. The `single-site-fasthtml-base` branch (an earlier pre-split state) came along into the monorepo as `mr/single-site-fasthtml-base`. The `design-v1-minimal-paper` branch (the earlier light/minimal fallback direction) was deliberately **not** migrated — it only exists in the old, archived `personal-webpage` repo now.
- The (gitignored, local-only) `README.md` has dev setup, deploy mechanics, and operational notes the user didn't want public.
- Monorepo-era deploy fully verified 2026-11-06: `deploy-mr.yml` deploys successfully, a
  repo-root-only push fires no deploy workflow at all, and a push touching only `mr/**`
  fires only `deploy-mr.yml` — not `deploy-mrs.yml`/`deploy-proxy-serve.yml`/`deploy-root.yml`.
- A Work project's report PDF is uploaded through `/admin/work`'s form (`app/routes/work.py`),
  not a path typed in by hand — it's stored under `SiteConfig.reports_dir` (default
  `data/reports/`, inside the `app-data` Docker volume) and served from a dedicated
  `/reports/{slug}.pdf` route, deliberately **not** `static/`: `static/` is baked into the
  image at build time, so anything written there at runtime would vanish on the next deploy.

## Content still to add (not yet written — confirm details with the user, don't invent)

- Only one school AI project (composer classification) is live so far; more exist.

This file, plus the user's own global `~/.claude/` rules (TDD, no wildcard imports, OOP where it fits, no `global` keyword, descriptive names), govern how work on this repo should proceed.
