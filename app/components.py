from fasthtml import common as Fast


def ingredient_table(names: list[str]) -> Fast.Table:
    """A specimen-style ingredient list — names only, deliberately no
    weight percentages (those are hers). Shared by the home page's
    featured tiles and the products overlay so a product's "label" looks
    the same everywhere it appears."""
    return Fast.Table(
        Fast.Caption("Ingredients", cls="sr-only"),
        Fast.Thead(Fast.Tr(Fast.Th("Ingredient", scope="col"))),
        Fast.Tbody(*(Fast.Tr(Fast.Th(name, scope="row")) for name in names)),
        cls="ingredient-table",
    )
