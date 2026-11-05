# kelseys.site

The bare `kelseys.site` domain: a public recipe book, filterable by name/ingredient/servings
with a trie-backed live-narrowing search, plus a "random recipe" draw that lets you exclude
ingredients you don't have and re-roll. The admin side (shared password) manages
ingredients/recipes and a family calendar.

## Project structure

```
app/
├── main.py              # app entry point: wires route modules together
├── config.py              # SiteConfig (env-driven settings)
├── auth.py                 # shared-password admin auth
├── db.py                    # fastlite Database + site_db singleton
├── models.py                 # Ingredient, Recipe, RecipeIngredient, CalendarEvent, RecurringEvent
├── trie.py                    # in-memory prefix search, rebuilt per request
├── layout.py                   # shared nav/header/footer shell
├── family.py                    # family member config (family.json)
├── calendar_grid.py               # month-grid rendering helpers
└── routes/
    ├── home.py, recipes.py, recipes_random.py     # public
    └── admin.py, admin_ingredients.py,
        admin_recipes.py, admin_calendar.py          # /admin/*, shared-password gated
```

## Run without Docker

```bash
uv sync
cp .env.example .env     # fill in SESSION_SECRET and ADMIN_PASSWORD
cp family.example.json family.json   # fill in real family member names/colors — never committed
.venv/bin/python -m app.main
```

Visit `http://localhost:8080`.

## Run with Docker Compose

```bash
cp .env.example .env
cp family.example.json family.json
docker compose up --build
```

## Running tests

```bash
uv sync
.venv/bin/pytest -q
```

Each test gets its own temp-file SQLite database (see `tests/conftest.py`) — no external
services needed, and the real `data/app.db` is never touched.

## Seeding sample data for local dev

```bash
.venv/bin/python -m scripts.seed_db
```

Inserts a handful of sample recipes/ingredients into whatever `DB_PATH` is currently
configured. Not idempotent — re-running duplicates rows.

## Deploy

Same pattern as the sibling `*.kelseys.site` repos: GitHub Actions runs the test suite, then
SSHes into the droplet as `deploy-root` (forced-command-restricted to `/opt/kelseys-root/deploy.sh`)
to pull and restart. See the parent `kelseys.site/.claude/CLAUDE.md` for the shared-infra
conventions and the manual one-time droplet/DNS/Caddy/GitHub-secrets setup this repo doesn't
script itself.
