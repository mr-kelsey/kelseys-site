# Scaffold `mrs.` — formulation-company site

## Context

`mrs.` is the next `*.kelseys.site` subdomain: a formulation company's site, sibling to the existing `mr.` resume/portfolio site under the same `kelseys.site` parent. It currently has no app code — just an empty directory plus `cli-version`, a symlink to an old standalone CLI tool (`/home/poppop/Developer/Python/wip/Examples/DDG`) that holds the company's actual formulation/costing business logic (ingredient costs, recipe-to-weight-percentage conversion, batch production costing). That logic needs to move into a proper web app; the CLI's own data model (parallel stringified-list columns in CSV, name-string lookups, no real keys) should **not** be ported as-is — it needs real normalized tables.

Confirmed decisions driving this plan:
- Build both the public marketing site and the admin-gated internal tool from day one (mirrors `mr.`'s public + `/admin` split).
- Mirror `mr.`'s stack exactly: FastHTML + fastlite/SQLite, Docker Compose, GitHub Actions deploy, its own git repo, its own `deploy-mrs` droplet user.
- The old CLI's CSV data is scratch data from building the tool — do not migrate it. New DB starts empty.
- Public sections at launch: Home, About, Contact, Product showcase (safe — no formulas/costs), Blog/journal — mirroring `mr.`'s Home/About/Contact/Work/Blog.

Verified directly against `mr.`'s source (`app/models.py`, `app/db.py`, `app/auth.py`) that the patterns below are accurate, not just agent-reported.

## Schema — `app/models.py`

Plain `@dataclass` models, `id: int = None` first, other fields default to `""`/`0.0` (never `None`) so fastlite infers column types — exactly `mr.`'s convention. No FK machinery in fastlite itself; foreign keys are plain `int` fields joined manually in Python.

```python
@dataclass
class Ingredient:
    id: int = None
    name: str = ""
    vendor: str = ""
    purchase_volume: float = 0.0   # amount per purchase unit
    volume_unit: str = ""          # oz / ml / g
    total_grams: float = 0.0       # grams per purchase unit -> cost/gram = purchase_price / total_grams
    purchase_price: float = 0.0
    created_at: str = ""

@dataclass
class Packaging:
    id: int = None
    name: str = ""
    supplier: str = ""
    purchase_volume: int = 0       # pieces per purchase lot
    purchase_price: float = 0.0    # total price for that lot -> cost/piece = purchase_price / purchase_volume
    moq_for_price: int = 0         # supplier's minimum order qty to unlock purchase_price at all (a
                                    # procurement constraint — NOT a customer sales-price tier). Per-piece
                                    # cost math is unaffected by this; it drives a separate "minimum spend
                                    # to restock" figure (see app/costing.py) so the admin can see the cash
                                    # commitment even when a batch only needs a fraction of the lot.
    created_at: str = ""

@dataclass
class Formula:
    id: int = None
    name: str = ""
    grams_per_unit: float = 0.0    # grams yielded per single finished unit
    notes: str = ""
    created_at: str = ""

@dataclass
class FormulaIngredient:          # join table, real PKs — replaces the old CLI's stringified parallel lists
    id: int = None
    formula_id: int = None
    ingredient_id: int = None
    percent: float = 0.0          # weight % of formula total

@dataclass
class Product:                    # public-safe showcase item, distinct from Formula
    id: int = None
    slug: str = ""
    name: str = ""
    description: str = ""
    photo: str = ""
    formula_id: int = None        # optional internal link; public routes must never read through it
    created_at: str = ""

@dataclass
class Post:                       # unchanged copy of mr.'s Post
    id: int = None
    slug: str = ""
    title: str = ""
    body: str = ""
    created_at: str = ""

@dataclass
class ContactMessage:             # unchanged copy of mr.'s ContactMessage
    id: int = None
    name: str = ""
    email: str = ""
    message: str = ""
    created_at: str = ""
```

No `cost_per_gram` column — always derived (`purchase_price / total_grams`), never stored, so it can't drift. `Product.formula_id` is admin-only convenience; public handlers in `products.py` must only ever query `site_db.products(...)`, never `Formula`/`FormulaIngredient` — enforce with a test.

`app/db.py`: same `Database` class shape as `mr.`'s (`app/db.py:7-18`), extended with `self.ingredients`, `self.packaging`, `self.formulas`, `self.formula_ingredients`, `self.products` alongside `self.posts`/`self.contact_messages`, each via `self.connection.create(Model, name="...", pk="id", transform=True)`.

## New module — `app/costing.py` (no `mr.` equivalent; pure functions, DB/web-independent)

Replaces the old CLI's `convert_recepeit` / `get_ingredients_needed` / `get_product_cost` / `get_weight_percentages`, with real objects instead of name-string lookups:

- `grams_for_quantity(ingredient, quantity) -> float` — `quantity * (ingredient.total_grams / ingredient.purchase_volume)`; guard `purchase_volume == 0`.
- `convert_recipe_to_percentages(entries: list[tuple[Ingredient, float]]) -> list[tuple[Ingredient, float]]` — raw qty → grams → percent-of-total. Caller turns the result into `FormulaIngredient` rows.
- `grams_needed_for_batch(formula, formula_ingredients_with_percent, *, unit_count=None, target_grams=None) -> dict[int, float]` — exactly one of `unit_count`/`target_grams` required.
- `cost_ingredients(grams_by_ingredient_id, ingredients_by_id) -> dict[int, float]`
- `cost_packaging(quantity_by_packaging_id, packaging_by_id) -> dict[int, float]`
- `summarize_batch_cost(ingredient_costs, packaging_costs) -> dict` — `{"ingredient_total", "packaging_total", "grand_total"}`
- `minimum_restock_cost(packaging: Packaging) -> float` — `packaging.moq_for_price * (packaging.purchase_price / packaging.purchase_volume)`: the cash she'd have to front to place a qualifying order with the supplier at all, regardless of how much a given batch actually needs. Surfaced in the batch-cost breakdown (`admin_costing.py`) per packaging line item, alongside (not folded into) the batch's actual packaging cost — e.g. "this batch needs $40 of tubes; restocking requires a $810 minimum order."

Test first (TDD, per global rule): percentages sum to ~100 within float tolerance; empty-input rejected; `grams_needed_for_batch` rejects both-or-neither of its two kwargs; divide-by-zero guard on `purchase_volume == 0`; `minimum_restock_cost` arithmetic, including `moq_for_price == purchase_volume` (the common case — see sample data note below).

## Routes — `app/routes/`

One file per section/entity, `router = Fast.APIRouter()`, `@router("/path")` `get()`/`post()`, registered in `app/main.py` — exactly `mr.`'s pattern (verified in `work.py`/`main.py`).

| File | Contents |
|---|---|
| `home.py`, `about.py` | public, copy `mr.`'s shape |
| `contact.py` | public GET/POST, copy `mr.`'s shape; reuses `app/email.py` (`ConsoleEmailSender`/`ResendEmailSender`) the same way `mr.` does |
| `blog.py` | public `/blog`, `/blog/{slug}` + admin CRUD — near-verbatim port of `mr.`'s `blog.py`, `Post` unchanged |
| `products.py` | public `/products`, `/products/{slug}` (name/description/photo only) + admin CRUD incl. optional `formula_id` picker never rendered publicly |
| `admin_ingredients.py`, `admin_packaging.py` | admin-only CRUD, **id-based routes** (`/admin/ingredients/{id}/edit`, etc.) — deliberately not name-based, unlike the old CLI's fragile `.lower()` matching |
| `admin_formulas.py` | CRUD for `Formula` + recipe editor. Edit form submits the whole recipe at once (`ingredient_id[]`/`quantity[]`), save deletes+reinserts all `FormulaIngredient` rows atomically via `convert_recipe_to_percentages` — percentages are relative to the whole set, not editable row-by-row. `/admin/formulas/{id}` is the breakdown view (replaces old `get_weight_percentages`) |
| `admin_costing.py` | the batch calculator — read-only computation, no persisted model, kept separate from `admin_formulas.py` since it's not resource CRUD: `/admin/formulas/{id}/cost` GET (form: `unit_count` OR `target_grams`, plus packaging qty rows) / POST (renders cost breakdown via `app/costing.py`, including each packaging line's `minimum_restock_cost` shown alongside its actual batch cost) |
| `admin.py`, `health.py` | copy `mr.`'s verbatim; `admin.py` dashboard links extended to new sections |

`app/main.py`: extend the registration loop; `app/layout.py` `NAV_LINKS`: Home, About, Products, Blog, Contact.

## Repo tree

```
mrs./
├── app/{config,db,models,auth,layout,errors,costing,email,main}.py
│   └── routes/{home,about,contact,blog,products,admin,admin_ingredients,
│                admin_packaging,admin_formulas,admin_costing,health}.py
├── static/css/site.css, static/img/favicon.png      # new brand — checkpoint, frontend-design skill
├── scripts/seed_db.py        # thin scaffold (empty REAL_* tuples, TODO) for parity, no real content yet
├── tests/  (mirrors mr.'s file-per-entity convention, see Test plan below)
├── Dockerfile, docker-entrypoint.sh                   # mirror mr.'s exactly
├── docker-compose.yml                                 # container_name: mrs-kelsey-app
├── .github/workflows/deploy.yml                        # mirror mr.'s — test job real, deploy job a stub
├── pyproject.toml   (name = "mrs-kelsey"), .env.example, .gitignore (+ `/cli-version`), .dockerignore
├── README.md (gitignored, local-only), .claude/CLAUDE.md (stub, points here)
└── cli-version -> .../DDG   # left in place, gitignored, reference-only; nothing in app/ imports it
```

`mr.` also has `tests/test_robots.py`, `test_static_security.py`, `test_session.py`, `test_zz_debug_routes.py` — infra-level (robots.txt, static-extension allowlist, session cookies), review and port verbatim during the infra-copy step rather than skipping silently.

## Naming — confirmed

| Thing | Value |
|---|---|
| `pyproject.toml` name | `mrs-kelsey` |
| Docker `container_name` | `mrs-kelsey-app` |
| Droplet deploy user | `deploy-mrs` |
| `/opt` path | `/opt/mrs-kelsey` |
| GitHub repo | `github.com/mr-kelsey/mrs-kelsey-personal-webpage` — same account as `mr.`'s repo (`mr-kelsey/personal-webpage`), disambiguated by the `mrs-kelsey-` prefix in the repo name itself |

Carrying forward as-is, not fixing: `mr.`'s own `deploy.yml` deploy job is currently a stub (`script: echo "deploying"`, not actually wired to `/opt/mr-kelsey/deploy.sh`) — mrs. mirrors that same stub rather than inventing real wiring the template doesn't have.

Confirmed: Contact form reuses `mr.`'s email abstraction (`app/email.py`, Resend-if-configured else console-log fallback) rather than going DB-only.

**Manual/infra checkpoints outside this plan's and any coding agent's reach**: provisioning `deploy-mrs` + its forced-command SSH key, writing the real server-side `/opt/mrs-kelsey/deploy.sh`, updating `proxy-serve/Caddyfile` with the `mrs.kelseys.site` block, the DNS record, creating the GitHub repo + pushing + adding its SSH secrets.

## Test plan (TDD — tests before implementation, per project rule)

1. `test_db.py` — table creation + insert/retrieve for all 7 models, mirroring `mr.`'s shape.
2. `test_costing.py` — pure-function tests, no `client` fixture needed (see validation list above).
3. `test_admin_auth.py` — copy `mr.`'s lockout/login tests verbatim.
4. `test_admin_ingredients.py`, `test_admin_packaging.py`, `test_admin_formulas.py`, `test_admin_products.py`, `test_admin_blog.py` — mirror `test_admin_work.py`: unauth redirect, authed 200, create/edit/delete round-trip, 404 on unknown id, logging assertions.
5. `test_admin_costing.py` — `/admin/formulas/{id}/cost` with both `unit_count` and `target_grams`; 404 unknown formula; auth-gated; asserts each packaging line shows its `minimum_restock_cost` alongside (not folded into) the batch's actual packaging cost.
6. `test_home.py`, `test_about.py`, `test_contact.py`, `test_blog.py`, `test_products.py` — 200s + 404s, plus a `test_products.py` guardrail asserting a `Product` linked to a `Formula` never leaks that formula's percentages/ingredients in the public response.
7. `test_errors.py`, `test_health.py`, `test_layout.py` + port the 4 unread infra tests from `mr.` listed above.

`conftest.py`: copy `mr.`'s `client`/`db`/`admin_client` fixtures verbatim — temp SQLite file per test, `monkeypatch` env vars, drop+reimport `app.*` to rebind the `site_db` singleton (required because it's created at import time) — this mechanism is site-agnostic. One assertion per test; names like `test_<verb>_<thing>_<expected_outcome>`.

## Build order, with checkpoints

1. Naming, email approach, GitHub destination, and MOQ handling are all confirmed above — no remaining pre-code checkpoint here.
2. Repo bootstrap: `git init`, `.gitignore` (incl. `/cli-version`), `.dockerignore`, `pyproject.toml`.
3. `test_db.py` → `app/models.py` + `app/db.py`.
4. Copy `app/config.py`, `app/auth.py`, `app/errors.py` verbatim; `test_admin_auth.py`, `test_errors.py`, `test_health.py` → `app/routes/health.py`, minimal `app/main.py`.
5. **Checkpoint**: visual direction (invoke `frontend-design` skill — `mr.`'s dark "case file" theme is persona-specific, not something to recolor-and-reuse) → `app/layout.py`, `static/css/site.css`, `static/img/favicon.png`.
6. `test_home.py`, `test_about.py`, `test_layout.py` → `home.py`, `about.py`. **Checkpoint**: real company copy/bio — don't invent.
7. `test_contact.py` → `contact.py` (+ `app/email.py` if reused).
8. `test_blog.py`, `test_admin_blog.py` → `blog.py`.
9. `test_admin_ingredients.py` → `admin_ingredients.py`; `test_admin_packaging.py` → `admin_packaging.py`.
10. `test_costing.py` (conversion half) → `app/costing.py` conversion fns → `test_admin_formulas.py` → `admin_formulas.py`.
11. `test_costing.py` (batch-cost half) → `app/costing.py` costing fns → `test_admin_costing.py` → `admin_costing.py`.
12. `test_products.py`, `test_admin_products.py` → `products.py` (incl. the public-exposure guardrail test).
13. Wire `admin.py` dashboard links + `main.py` registration loop + `NAV_LINKS`.
14. Infra scaffold: `Dockerfile`, `docker-entrypoint.sh`, `docker-compose.yml`, `deploy.yml` (stub deploy job), `.env.example`, `README.md`. Run `uv sync` + full `pytest` locally.
15. **Checkpoint (manual/infra)**: GitHub repo + push, droplet user/deploy.sh provisioning, `proxy-serve/Caddyfile` update, DNS.
16. Stub `mrs./.claude/CLAUDE.md` (full version once the site is actually built out — out of scope here; already in place as a stub pointing here).

## Critical files

- `app/models.py`, `app/db.py`, `app/costing.py`
- `app/routes/admin_formulas.py`, `app/routes/admin_costing.py`, `app/routes/products.py`
- `tests/test_costing.py`, `tests/test_products.py`
- `docker-compose.yml`

## Verification

- `.venv/bin/pytest -q` green at each build-order step (tests written first, per step, before the code that satisfies them).
- Manual smoke test via the `run` skill once routes exist: load `/`, `/products`, `/blog`, `/contact`; log into `/admin`, create an ingredient + packaging item + formula with a recipe, confirm percentages sum to 100 in the breakdown view, run a batch cost calc, confirm a `Product` page never renders formula/percent/cost data.
- `docker compose build` succeeds locally before any deploy-pipeline work.
