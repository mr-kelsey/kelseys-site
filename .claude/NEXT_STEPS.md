# mrs. — next steps

The initial-build plan (schema, routes, infra scaffold) is done and its
planning doc has been retired — see `.claude/CLAUDE.md` for what's left
of it (naming facts, data-safety invariants, the still-outstanding
manual deploy checklist). This file is the live queue of what's decided
but not yet built, agreed with the stakeholder on 2026-10-31/11-01.
Items are deleted from here once they land, not recorded — git history
is the record of what was done and why. Read `.claude/CLAUDE.md` first
for the current state of the app before working from this list.

## Category taxonomy

The field and the UI (admin input, public grouping) exist; the actual
category *names* are still real business content — don't invent them.
She can start typing whatever categories make sense to her in
`/admin/products/*/edit`; existing products will show as
"Uncategorized" until then.

## Formula/product data: synthetic first, her real data later — and only via her own admin entry

**Business constraint, not a technical one:** the client does not want
to disclose any formulas beyond the two already shown on the public
site (Lip Balm, Bright Lip Balm) — proportions are the trade secret
(see the data-safety invariant in `.claude/CLAUDE.md`; plain ingredient
*names* are fine to show once she links a formula to a product).

- The admin CRUD for ingredients/packaging/formulas/products already
  exists (`admin_ingredients.py`, `admin_packaging.py`,
  `admin_formulas.py`, and the admin routes inside `products.py`) — the
  real content pipeline is: she logs into `/admin` and enters her own
  products/formulas/categories directly. The public site (home page
  workbench sample, `/products` listing) picks up whatever she enters
  automatically — confirmed via a synthetic-data pass through the full
  pipeline, no code change needed when she adds a product or formula.
- Before handing the admin off to her: do one more pass confirming the
  percent-leak-guard test still passes after any further changes here,
  since we won't be reviewing her real entries after that point the way
  we'd review a PR.

## Smaller carried-forward items

- **Real credentials**: the About section's Credentials block
  (`app/routes/home.py`) is intentionally placeholder text
  (`[Certification — to be added]` etc.) pending real specifics from
  the stakeholder.
- **More partner names**: Partners section currently names only "Drop
  Dead Gorgeous" (real, confirmed) plus two honestly-labeled "more
  partners — details coming" slots. Do not invent additional names.
