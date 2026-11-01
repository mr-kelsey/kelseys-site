# mrs. (formulation company site)

Public site + admin tool for Kaleidoscopic Creations (Mrs. Kelsey's
formulation company). Built: schema, costing module, admin CRUD for
ingredients/packaging/formulas/products/blog, and — as of 2026-10-31 —
the real visual identity ("Apothecary Reveal") and a fully content-real
home page. Not yet built: the home page's Products-section redesign,
folding the About page into the home page, and real formula/product
data entry — see `.claude/NEXT_STEPS.md` for the current,
agreed-but-not-yet-built list and read it before starting any new
implementation work here. This repo is one of several `*.kelseys.site`
subdomains under one project root — see the parent
`kelseys.site/.claude/CLAUDE.md` for the overall layout and shared-infra
conventions.

- Visual identity: moss/berry/ochre on bone paper, Fraunces + Source
  Serif 4 + Space Mono, chosen from a round of mockups reviewed with the
  stakeholder. Lives in `app/layout.py` (shared chrome, applies
  site-wide) and `static/css/site.css`. The home page
  (`app/routes/home.py`) additionally renders a fixed, full-viewport
  mark animation behind its content, shown through transparent "window"
  gaps only it currently has.
- Data-safety invariant: `Product.formula_id` (`app/models.py`) is
  admin-only convenience — public routes in `products.py` must only
  ever query `site_db.products(...)`, never `Formula`/`FormulaIngredient`.
  Enforced by `tests/test_products.py`'s two leak-guard tests; don't
  remove or weaken them.
- No `cost_per_gram` column anywhere — always derived
  (`purchase_price / total_grams`) in `app/costing.py`, never stored, so
  it can't drift from the source numbers.
- Naming, confirmed: `pyproject.toml` name `mrs-kelsey`; Docker
  `container_name` `mrs-kelsey-app`; droplet deploy user `deploy-mrs`;
  `/opt` path `/opt/mrs-kelsey`; GitHub repo
  `github.com/mr-kelsey/mrs-kelsey-personal-webpage` (same account as
  `mr.`'s `mr-kelsey/personal-webpage`, disambiguated by the
  `mrs-kelsey-` prefix). `mr.`'s own `deploy.yml` deploy job is a stub
  (`script: echo "deploying"`, not wired to a real `deploy.sh`) —
  `mrs.` mirrors that same stub deliberately rather than inventing real
  wiring the template doesn't have.
- Deployment — not yet done, outside any coding agent's reach:
  provisioning `deploy-mrs` + its forced-command SSH key, writing the
  real server-side `/opt/mrs-kelsey/deploy.sh`, updating
  `proxy-serve/Caddyfile` with the `mrs.kelseys.site` block, the DNS
  record, creating the GitHub repo + pushing + adding its SSH secrets.

`cli-version` (a symlink to an unrelated-looking path outside this repo) holds the old CLI tool whose formulation/costing logic (ingredient costs, recipe-to-weight-percentage conversion, batch production costing) was ported into `app/costing.py` with real normalized tables instead of the CLI's stringified-list CSV columns — it's gitignored and reference-only, not something `app/` should import from directly.
