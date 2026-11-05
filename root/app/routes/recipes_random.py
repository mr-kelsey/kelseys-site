from random import choice

from fasthtml import common as Fast

from app.db import site_db
from app.layout import site_layout

router = Fast.APIRouter()

EXCLUDED_INGREDIENTS_SESSION_KEY = "excluded_ingredient_ids"


def _random_recipe_url(name: str, servings: str, ingredient_id: str) -> str:
    params = {"name": name, "servings": servings, "ingredient_id": ingredient_id}
    query = "&".join(f"{key}={value}" for key, value in params.items() if value)
    return "/recipes/random" + (f"?{query}" if query else "")


def _exclude_ingredient_form(
    ingredient_id: int, name: str, servings: str, filter_ingredient_id: str
) -> Fast.Form:
    return Fast.Form(
        Fast.Input(type="hidden", name="name", value=name),
        Fast.Input(type="hidden", name="servings", value=servings),
        Fast.Input(type="hidden", name="filter_ingredient_id", value=filter_ingredient_id),
        Fast.Button("I don't have this", type="submit"),
        method="post",
        action=f"/recipes/random/exclude/{ingredient_id}",
    )


def _accept_form(recipe_id: int) -> Fast.Form:
    return Fast.Form(
        Fast.Input(type="hidden", name="recipe_id", value=str(recipe_id)),
        Fast.Button("Accept this recipe", type="submit"),
        method="post",
        action="/recipes/random/accept",
    )


def _reset_form() -> Fast.Form:
    return Fast.Form(
        Fast.Button("Start over with every ingredient", type="submit"),
        method="post",
        action="/recipes/random/reset",
    )


@router("/recipes/random")
def get(session, name: str = "", ingredient_id: str = "", servings: str = ""):
    excluded = tuple(session.get(EXCLUDED_INGREDIENTS_SESSION_KEY, []))
    pool = site_db.filtered_recipes(
        name=name.strip() or None,
        ingredient_id=int(ingredient_id) if ingredient_id else None,
        servings=int(servings) if servings else None,
        excluded_ingredient_ids=excluded,
    )
    if not pool:
        return site_layout(
            "Random Recipe",
            Fast.Div(
                Fast.H1("Random Recipe"),
                Fast.P("No recipes left in this pool. Reset your exclusions or change filters."),
                _reset_form(),
                cls="random-recipe",
            ),
        )
    recipe = choice(pool)
    links = site_db.recipe_ingredients(where="recipe_id = ?", where_args=[recipe.id])
    ingredient_rows = []
    for link in links:
        ingredient = site_db.ingredients.get(link.ingredient_id)
        ingredient_rows.append(
            Fast.Li(
                f"{link.quantity} {ingredient.name}".strip(),
                _exclude_ingredient_form(ingredient.id, name, servings, ingredient_id),
            )
        )
    return site_layout(
        "Random Recipe",
        Fast.Div(
            Fast.H1(recipe.name),
            Fast.P(f"Serves {recipe.servings}", cls="servings"),
            Fast.Ul(*ingredient_rows),
            Fast.Pre(recipe.instructions),
            _accept_form(recipe.id),
            Fast.A("Reroll", href=_random_recipe_url(name, servings, ingredient_id)),
            cls="random-recipe",
        ),
    )


@router("/recipes/random/exclude/{ingredient_id}")
def post(
    ingredient_id: int,
    session,
    name: str = "",
    servings: str = "",
    filter_ingredient_id: str = "",
):
    excluded = session.get(EXCLUDED_INGREDIENTS_SESSION_KEY, [])
    if ingredient_id not in excluded:
        excluded.append(ingredient_id)
    session[EXCLUDED_INGREDIENTS_SESSION_KEY] = excluded
    return Fast.Redirect(_random_recipe_url(name, servings, filter_ingredient_id))


@router("/recipes/random/accept")
def post(recipe_id: int, session):
    session[EXCLUDED_INGREDIENTS_SESSION_KEY] = []
    return Fast.Redirect(f"/recipes/{recipe_id}")


@router("/recipes/random/reset")
def post(session):
    session[EXCLUDED_INGREDIENTS_SESSION_KEY] = []
    return Fast.Redirect("/recipes/random")
