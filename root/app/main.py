from fasthtml.common import fast_app, reg_re_param
from fasthtml.xtend import robots_txt

from app.config import SiteConfig
from app.errors import not_found
from app.routes import (
    admin,
    admin_calendar,
    admin_ingredients,
    admin_recipes,
    health,
    home,
    recipes,
    recipes_random,
)

config = SiteConfig()
app, route = fast_app(
    pico=False, exception_handlers={404: not_found}, secret_key=config.session_secret
)

# recipes_random registers literal paths under /recipes/random/... that must be
# matched before recipes' /recipes/{recipe_id} -- that catch-all has no int path
# converter, so it would otherwise greedily match "/recipes/random" itself.
for routes_module in (
    health,
    home,
    admin,
    admin_ingredients,
    admin_recipes,
    admin_calendar,
    recipes_random,
    recipes,
):
    routes_module.router.to_app(app)

robots_txt(app, disallow_paths=["/admin"])

# fast_app() auto-registers a catch-all static route matching *any* path
# under the whole working directory for ~50 extensions — far more than
# this site serves. Drop it and register a narrower one covering only
# what's actually in static/, so a stray file elsewhere can't become
# silently, unauthenticatedly public.
SITE_STATIC_EXTENSIONS = "ico css js png jpg jpeg svg webp woff woff2".split()
reg_re_param("site_static", "|".join(SITE_STATIC_EXTENSIONS))

static_catch_all = next(r for r in app.routes if r.name == "static_route_exts_get")
app.routes.remove(static_catch_all)
app.static_route_exts(exts="site_static")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)
