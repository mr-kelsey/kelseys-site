from fastlite import NotFoundError
from fasthtml import common as Fast

from app.db import site_db
from app.layout import site_layout
from app.models import Recipe
from app.trie import Trie

router = Fast.APIRouter()

RESULTS_CONTAINER_ID = "recipe-results"


def _ingredient_options() -> list[Fast.Option]:
    return [Fast.Option("Any ingredient", value="")] + [
        Fast.Option(ingredient.name, value=str(ingredient.id))
        for ingredient in site_db.ingredients(order_by="name")
    ]


def _filter_form(name: str, ingredient_id: str, servings: str, q: str) -> Fast.Form:
    live_search = {
        "hx_get": "/recipes/results",
        "hx_target": f"#{RESULTS_CONTAINER_ID}",
    }
    return Fast.Form(
        Fast.Input(
            name="name",
            placeholder="Recipe name",
            value=name,
            hx_trigger="input changed delay:200ms",
            **live_search,
        ),
        Fast.Select(
            *_ingredient_options(),
            name="ingredient_id",
            value=ingredient_id,
            hx_trigger="change",
            **live_search,
        ),
        Fast.Input(
            name="servings",
            type="number",
            min="1",
            placeholder="Servings",
            value=servings,
            hx_trigger="input changed delay:200ms",
            **live_search,
        ),
        Fast.Input(
            name="q",
            placeholder="Narrow results by name...",
            value=q,
            hx_trigger="input changed delay:150ms",
            **live_search,
        ),
    )


def _recipe_result_row(recipe: Recipe) -> Fast.Li:
    return Fast.Li(
        Fast.A(recipe.name, href=f"/recipes/{recipe.id}"),
        Fast.Span(f"serves {recipe.servings}", cls="servings"),
    )


def _recipe_results(recipes: list[Recipe]):
    if not recipes:
        return Fast.P("No recipes match.", id=RESULTS_CONTAINER_ID)
    return Fast.Ul(
        *(_recipe_result_row(recipe) for recipe in recipes),
        id=RESULTS_CONTAINER_ID,
        cls="recipe-results",
    )


def _candidate_recipes(name: str, ingredient_id: str, servings: str, q: str) -> list[Recipe]:
    candidates = site_db.filtered_recipes(
        name=name.strip() or None,
        ingredient_id=int(ingredient_id) if ingredient_id else None,
        servings=int(servings) if servings else None,
    )
    q = q.strip()
    if not q:
        return candidates
    return Trie([(recipe.name, recipe) for recipe in candidates]).search_prefix(q)


@router("/recipes")
def get(name: str = "", ingredient_id: str = "", servings: str = "", q: str = ""):
    candidates = _candidate_recipes(name, ingredient_id, servings, q)
    return site_layout(
        "Recipes",
        Fast.H1("Recipes"),
        _filter_form(name, ingredient_id, servings, q),
        _recipe_results(candidates),
    )


@router("/recipes/results")
def get(name: str = "", ingredient_id: str = "", servings: str = "", q: str = ""):
    return _recipe_results(_candidate_recipes(name, ingredient_id, servings, q))


@router("/recipes/{recipe_id}")
def get(recipe_id: int):
    try:
        recipe = site_db.recipes.get(recipe_id)
    except NotFoundError:
        raise Fast.HTTPException(status_code=404)
    links = site_db.recipe_ingredients(where="recipe_id = ?", where_args=[recipe_id])
    ingredient_rows = []
    for link in links:
        try:
            ingredient = site_db.ingredients.get(link.ingredient_id)
        except NotFoundError:
            continue
        ingredient_rows.append(Fast.Li(f"{link.quantity} {ingredient.name}".strip()))
    return site_layout(
        recipe.name,
        Fast.Div(
            Fast.H1(recipe.name),
            Fast.P(f"Serves {recipe.servings}", cls="servings"),
            Fast.Ul(*ingredient_rows),
            Fast.Pre(recipe.instructions),
            Fast.P(recipe.notes) if recipe.notes else None,
            cls="recipe-detail",
        ),
    )
