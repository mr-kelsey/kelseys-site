from dataclasses import dataclass


@dataclass
class Ingredient:
    id: int = None
    name: str = ""
    created_at: str = ""


@dataclass
class Recipe:
    id: int = None
    name: str = ""
    servings: int = 1
    instructions: str = ""
    notes: str = ""
    created_at: str = ""


@dataclass
class RecipeIngredient:
    id: int = None
    recipe_id: int = None
    ingredient_id: int = None
    quantity: str = ""


@dataclass
class CalendarEvent:
    id: int = None
    owner_id: str = ""
    title: str = ""
    start_date: str = ""
    end_date: str = ""
    start_time: str | None = None
    end_time: str | None = None
    notes: str | None = None
    is_critical: int = 0
    created_at: str = ""


@dataclass
class RecurringEvent:
    id: int = None
    title: str = ""
    month: int = 1
    day: int = 1
    created_at: str = ""
