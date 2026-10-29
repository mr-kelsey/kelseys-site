from fasthtml.common import fast_app, reg_re_param
from fasthtml.xtend import robots_txt

from app.config import SiteConfig
from app.errors import not_found
from app.routes import (
    about,
    admin,
    admin_costing,
    admin_formulas,
    admin_ingredients,
    admin_packaging,
    blog,
    contact,
    health,
    home,
    products,
)

config = SiteConfig()
app, route = fast_app(
    pico=False, exception_handlers={404: not_found}, secret_key=config.session_secret
)

for routes_module in (
    home,
    about,
    products,
    blog,
    contact,
    health,
    admin,
    admin_ingredients,
    admin_packaging,
    admin_formulas,
    admin_costing,
):
    routes_module.router.to_app(app)

robots_txt(app, disallow_paths=["/admin"])

# fast_app() auto-registers a catch-all static route matching *any* path
# under the whole working directory (not just static/) for ~50 extensions,
# including txt/csv/xml/yaml/html/doc — far more than this site serves.
# Drop it and register a narrower one covering only what's actually in
# static/, so a stray file dropped anywhere under app/ or scripts/ later
# can't become silently, unauthenticatedly public.
SITE_STATIC_EXTENSIONS = "ico css js png jpg jpeg svg webp woff woff2 pdf".split()
reg_re_param("site_static", "|".join(SITE_STATIC_EXTENSIONS))

static_catch_all = next(r for r in app.routes if r.name == "static_route_exts_get")
app.routes.remove(static_catch_all)
app.static_route_exts(exts="site_static")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8080, reload=True)
