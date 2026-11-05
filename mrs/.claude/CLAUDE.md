# mrs. (formulation company site)

Public site + admin tool for Kaleidoscopic Creations (Mrs. Kelsey's
formulation company). Built: schema, costing module, admin CRUD for
ingredients/packaging/formulas/products/blog, the real visual identity
("Apothecary Reveal", 2026-10-31), a fully content-real home page, and —
as of 2026-11-02 — the About fold, the overlay-driven Products page,
product categories, a DB-driven home page workbench sample, synthetic
seed data, and a real favicon. Still open: real formula/product/category
content from the stakeholder (synthetic data only so far) — see
`.claude/NEXT_STEPS.md` for the current, agreed-but-not-yet-built list
and read it before starting any new implementation work here. This repo
is one of several `*.kelseys.site` subdomains under one project root —
see the parent `kelseys.site/.claude/CLAUDE.md` for the overall layout
and shared-infra conventions.

- Visual identity: moss/berry/ochre on bone paper, Fraunces + Source
  Serif 4 + Space Mono, chosen from a round of mockups reviewed with the
  stakeholder. Lives in `app/layout.py` (shared chrome, applies
  site-wide) and `static/css/site.css`. The home page
  (`app/routes/home.py`) additionally renders a fixed, full-viewport
  mark animation behind its content, shown through transparent "window"
  gaps only it currently has.
- Data-safety invariant (revised 2026-11-02 — the original version of
  this rule banned public routes from touching `Formula`/
  `FormulaIngredient` at all, which also blocked showing a product's
  plain ingredient list, the same info a cosmetic product's label
  discloses by law; that was overcorrecting): the trade secret is the
  *recipe* — `FormulaIngredient.percent`, i.e. proportions/ratios —
  never the mere fact that an ingredient is used. Public routes in
  `products.py` may resolve a linked formula down to ingredient
  *names* only, via `_formula_ingredient_names()`, which never reads
  or returns `.percent`. `Product.formula_id` itself stays off any
  public response (it's an internal id, not content). Enforced by
  `tests/test_products.py`'s percent leak-guard test — don't remove or
  weaken that one; the old names leak-guard test was replaced with a
  names-ARE-shown test to match this correction.
- No `cost_per_gram` column anywhere — always derived
  (`purchase_price / total_grams`) in `app/costing.py`, never stored, so
  it can't drift from the source numbers.
- Naming, confirmed: `pyproject.toml` name `mrs-kelsey`; Docker
  `container_name` `mrs-kelsey-app`; droplet deploy user `deploy-mrs`;
  `/opt` path `/opt/mrs-kelsey`; GitHub repo
  `github.com/mr-kelsey/mrs-kelsey-personal-webpage` (same account as
  `mr.`'s `mr-kelsey/personal-webpage`, disambiguated by the
  `mrs-kelsey-` prefix).
- Deployment: **live**, fully wired. GitHub Actions (`deploy.yml`) runs
  the test suite on every push to `main` and then SSHes into the
  droplet as `deploy-mrs`; Caddy (`proxy-serve/Caddyfile`) has the
  `mrs.kelseys.site` block reverse-proxying to `mrs-kelsey-app:8080`;
  DNS resolves and `https://mrs.kelseys.site/` serves 200 (verified
  2026-11-01). The deploy job's own `script:` is just
  `echo "deploying"`, same stub `mr.` uses — that's fine, not a gap:
  `deploy-mrs`'s SSH key is forced-command-restricted on the droplet to
  always run the real `/opt/mrs-kelsey/deploy.sh` regardless of what
  command the Action sends, per the parent repo's cross-site SSH
  convention. Don't "fix" the stub text thinking it's broken.
  **Caveat:** pushing to `main` is what ships a release — confirm with
  whoever's driving before pushing a commit, same as any other deploy.

`cli-version` (a symlink to an unrelated-looking path outside this repo) holds the old CLI tool whose formulation/costing logic (ingredient costs, recipe-to-weight-percentage conversion, batch production costing) was ported into `app/costing.py` with real normalized tables instead of the CLI's stringified-list CSV columns — it's gitignored and reference-only, not something `app/` should import from directly.
