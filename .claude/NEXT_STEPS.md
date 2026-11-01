# mrs. — next steps

The initial-build plan (schema, routes, infra scaffold) is done and its
planning doc has been retired — see `.claude/CLAUDE.md` for what's left
of it (naming facts, data-safety invariants, the still-outstanding
manual deploy checklist). This file is the live list of what's decided
but not yet built, agreed with the stakeholder on 2026-10-31/11-01. Read
`.claude/CLAUDE.md` first for the current state of the app before working
from this list.

## 1. Fold "About" into the home page — no standalone About page

Decision: the nav's "About" link should go to the home page's own
`#about` section (already built — formulator bio + credentials block in
`app/routes/home.py`), not to a separate page.

Open sub-question to resolve during implementation: does the standalone
`/about` route get deleted outright, or kept as a redirect to `/#about`
(e.g. for anything that already links to it directly)? Either is fine —
just pick one and update `tests/test_about.py` to match instead of
leaving it asserting on dead content.

Touches: `app/layout.py` (`NAV_LINKS`), `app/routes/about.py`,
`tests/test_about.py`, `tests/test_layout.py`.

## 2. Redesign the home page's Products section

The section currently has two parts (`app/routes/home.py`, `_products()`):
upper = the two real lip balm "specimen" tiles (ingredient lists, no
percentages); lower = three hardcoded "workbench" tiles (Facial Regimen,
After-Tattoo Care, Massage Oil).

Target behavior for the lower "workbench" part, once the DB has real
`Product` rows (see §3 — this is blocked on that):

- Pull a **random** sample of products from the DB instead of hardcoded
  tiles.
- Cap the count **responsively** — fewer tiles on narrow screens, more
  on wide ones. Likely approach: render a somewhat generous random
  sample server-side (e.g. 6), and let CSS hide tiles past a per-breakpoint
  limit (`nth-child` + `display: none` at each `@media` step) rather than
  trying to infer viewport size server-side. Exact per-breakpoint counts
  are TBD — pick something reasonable and adjust once it's visually
  checked (see `run` skill / the Playwright-based screenshot tooling
  used during the visual-direction pass for how to verify this without
  guessing).
- Each tile becomes a **single link covering the whole tile** (not just
  a text link inside it) to the dedicated Products page.
- Needs a **category/sort system** — the `Product` model
  (`app/models.py`) has no category field yet; add one (plain string is
  probably enough to start, no need for a separate table unless a real
  need for nested/multi categories shows up) and decide the actual
  taxonomy. Don't invent the categories — that's real business content,
  same rule as formula data (see §3).

## 3. Products page becomes an overlay-driven detail view

Target UX: `/products` lists all products. Clicking a product (from the
home page workbench tiles, or from the list itself) opens an overlay
showing that product's ingredients + marketing blurb, **without losing
the list underneath** — closing the overlay goes back to the full list,
not a separate blank page.

Suggested implementation shape (not committed, just the obvious fit for
this stack): keep `/products/{slug}` as a real, shareable URL, but have
it render the *same* products-list page with the matching product's
overlay already open server-side, rather than a totally separate
detail-only page — this avoids needing client-side routing/JS to make
the overlay state shareable, consistent with the rest of the site being
server-rendered. `/products` with no slug renders the list with no
overlay open.

Touches: `app/routes/products.py` (both the public `GET /products` and
`GET /products/{slug}` handlers currently do two unrelated things —
list vs. single-product page — and need to converge), `static/css/site.css`
(overlay/modal styling), `tests/test_products.py`.

## 4. Formula/product data: synthetic first, her real data later — and only via her own admin entry

**Business constraint, not a technical one — this shapes how the above
gets built and tested:** the client does not want to disclose any
formulas beyond the two already shown on the public site (Lip Balm,
Bright Lip Balm). The Facial Regimen / After-Tattoo Care / Massage Oil
tiles, and anything else she makes, are real products but their
*formulas* are not ours to enter or see.

Consequences:

- `scripts/seed_db.py` (currently a scaffold with empty `REAL_*` tuples,
  never filled in) should be filled with clearly **synthetic** placeholder
  ingredients/formulas/products for local dev and automated tests —
  never anything resembling her real recipes, and never asked of her
  just to unblock testing.
- The admin CRUD for ingredients/packaging/formulas/products already
  exists (`admin_ingredients.py`, `admin_packaging.py`,
  `admin_formulas.py`, and the admin routes inside `products.py`) — the
  real content pipeline is: she logs into `/admin` and enters her own
  formulas directly. The public site (home page workbench tiles,
  `/products` listing) must pick up whatever she enters **automatically**
  — no code change should be needed on our end when she adds a new
  product or formula.
- Practical implication for us: do a thorough pass with synthetic data
  exercising the full admin → public-site pipeline (create a formula,
  link it to a product, confirm it shows up correctly on the home page
  workbench sample and the `/products` overlay, confirm percentages/
  ingredient math still never leaks publicly per the existing guardrail
  in `tests/test_products.py`) **before** handing the admin off to her,
  since we won't be reviewing her real entries after that point the way
  we'd review a PR.

## 5. Spotlight animation: smooth the crossfade into a radial propagation

Current behavior (`.frame-layer` / `@keyframes frameFade` in
`static/css/site.css`): all ten frames crossfade via a uniform opacity
change, so it reads as the mark's colors flashing/swapping rather than
flowing.

Requested behavior: the color change should visibly start at the
**center** of the mark and propagate **outward** to the edge, fast
enough that the center has already started the *next* transition by the
time the previous one reaches the edge — a continuous outward ripple
rather than a flat fade. Stakeholder flagged this as something they're
not sure is achievable — it is, but it's a genuinely different technique
from the current one, not a tweak to the existing keyframes:

- The uniform `opacity: 0 → 1 → 0` crossfade can't produce this by
  itself — it needs each frame's *reveal* to be driven by an animated
  mask (e.g. `mask-image: radial-gradient(...)` whose radius keyframes
  from 0% to 100% over the frame's active window) instead of a plain
  opacity fade, so the new frame visibly "grows" from the center across
  the old one.
- Getting the next frame's center to start changing before the previous
  ring finishes reaching the edge means overlapping two animated masks
  (outgoing frame's reveal-mask growing while still finishing, incoming
  frame's reveal-mask starting) rather than the current simple 2-second-
  stagger-of-identical-keyframes approach — more fiddly timing, worth
  prototyping in isolation (a standalone scratch HTML file, same
  approach as the original design-proposal mockups) before touching the
  real site, and verifying with the `screenshot` skill
  (`~/.claude/skills/screenshot` — screenshots a local file or a running
  localhost URL via a persistent Playwright setup; use `inspect_page.py`'s
  scroll-to-selector capture, not a full-page shot, since this is exactly
  the `position: fixed` case it exists for) at a few points through one
  cycle rather than eyeballing it live.
- Do not let this regress the two already-fixed, confirmed-working
  things about this layer: no `filter` + `mix-blend-mode` combination on
  the same element (silently breaks the blend, confirmed in testing),
  and the `mix-blend-mode: multiply` erasure needs the solid `--paper`
  backdrop on `.reveal-stage` to keep working once it's inside
  `position: fixed`.

## 6. Smaller carried-forward items

- **Favicon**: `app/layout.py` currently points the favicon link at
  `logo-pastel.png` directly (the full-size mark, not a proper cropped/
  optimized favicon asset). Fine as a placeholder, not fine long-term.
- **Real credentials**: the About section's Credentials block
  (`app/routes/home.py`) is intentionally placeholder text
  (`[Certification — to be added]` etc.) pending real specifics from
  the stakeholder.
- **More partner names**: Partners section currently names only "Drop
  Dead Gorgeous" (real, confirmed) plus two honestly-labeled "more
  partners — details coming" slots. Do not invent additional names.
