# mrs. — next steps

The initial-build plan (schema, routes, infra scaffold) is done and its
planning doc has been retired — see `.claude/CLAUDE.md` for what's left
of it (naming facts, data-safety invariants, the still-outstanding
manual deploy checklist). This file is the live list of what's decided
but not yet built, agreed with the stakeholder on 2026-10-31/11-01, and
updated as items land. Read `.claude/CLAUDE.md` first for the current
state of the app before working from this list.

## Done (2026-11-02)

- **About folded into the home page.** `/about` now redirects to
  `/#about`; `NAV_LINKS` points there directly. See `app/routes/about.py`,
  `app/layout.py`.
- **Data-safety invariant corrected.** The old rule ("public routes
  must never touch `Formula`/`FormulaIngredient`") overcorrected — it
  also blocked showing a product's plain ingredient list, which isn't
  secret (a cosmetic label discloses that by law; only the *proportions*
  are the trade secret). Public routes may now resolve a linked
  formula's ingredient **names** via `_formula_ingredient_names()` in
  `app/routes/products.py`, which never reads `.percent`. See the
  revised invariant in `.claude/CLAUDE.md`.
- **Products page is now overlay-driven.** `GET /products` renders the
  full list, grouped and sorted by category; `GET /products/{slug}`
  renders the same list plus that product's overlay (name, photo,
  description, ingredient names if formula-linked) on top, closable
  back to the plain list. See `app/routes/products.py`,
  `static/css/site.css` (`.products-overlay` etc.).
- **Category field added to `Product`** (`app/models.py`,
  plain string, admin free-text in `_product_form`) — taxonomy values
  themselves are still hers to decide/enter, we only built the
  mechanism. `/products` groups by it (falling back to "Uncategorized"
  for blank); unset on the home page workbench sample for now, see
  below.
- **Home page workbench section is now DB-driven.** `_products()` in
  `app/routes/home.py` pulls a random sample (`WORKBENCH_SAMPLE_SIZE =
  6`) of `Product` rows instead of the three hardcoded tiles (Facial
  Regimen / After-Tattoo Care / Massage Oil), each tile a single link
  to `/products/{slug}`. Responsive cap via `nth-child` + `display:
  none` in `static/css/site.css`, reusing the existing `.tile-row--blurb`
  breakpoints. Section (heading + row) omits itself entirely when no
  products exist.
  **Deploy caveat:** until real `Product` rows exist, this section is
  empty on the live site — it no longer names Facial Regimen/
  After-Tattoo Care/Massage Oil at all. Don't ship this to `main`
  without either those three (or equivalents) entered via `/admin`
  first, or being fine with a sparse/empty workbench section in the
  meantime.
- **`scripts/seed_db.py` filled with synthetic data** — ingredients,
  packaging, one formula (percentages summing to 100), two products
  (one formula-linked, one not), one blog post, all clearly named
  `Synthetic ... (Dev Placeholder)`. Tested in `tests/test_seed_db.py`.
  Not idempotent (unchanged from before) — re-running duplicates rows.
- **Favicon**: `static/img/favicon.png`, a trimmed/cropped 180×180 of
  the mark (not the 1MB full-size logo), referenced from
  `app/layout.py`.

## Still open

### Category taxonomy

The field and the UI (admin input, public grouping) exist; the actual
category *names* are still real business content — don't invent them.
She can start typing whatever categories make sense to her in
`/admin/products/*/edit`; existing products will show as
"Uncategorized" until then.

### Formula/product data: synthetic first, her real data later — and only via her own admin entry

**Business constraint, not a technical one:** the client does not want
to disclose any formulas beyond the two already shown on the public
site (Lip Balm, Bright Lip Balm) — proportions are the trade secret
(see the corrected data-safety invariant above; plain ingredient
*names* are fine to show once she links a formula to a product).

- The admin CRUD for ingredients/packaging/formulas/products already
  exists (`admin_ingredients.py`, `admin_packaging.py`,
  `admin_formulas.py`, and the admin routes inside `products.py`) — the
  real content pipeline is: she logs into `/admin` and enters her own
  products/formulas/categories directly. The public site (home page
  workbench sample, `/products` listing) picks up whatever she enters
  automatically — confirmed via the synthetic-data pass above, no code
  change needed when she adds a product or formula.
- Before handing the admin off to her: do one more pass confirming the
  percent-leak-guard test still passes after any further changes here,
  since we won't be reviewing her real entries after that point the way
  we'd review a PR.

### Smaller carried-forward items

- **Real credentials**: the About section's Credentials block
  (`app/routes/home.py`) is intentionally placeholder text
  (`[Certification — to be added]` etc.) pending real specifics from
  the stakeholder.
- **More partner names**: Partners section currently names only "Drop
  Dead Gorgeous" (real, confirmed) plus two honestly-labeled "more
  partners — details coming" slots. Do not invent additional names.
