from datetime import datetime, timezone

from fastlite import database

from app.config import SiteConfig
from app.models import CalendarEvent, Ingredient, Recipe, RecipeIngredient, RecurringEvent


def _normalize_event_fields(title, start_date, end_date, start_time, end_time, notes, is_critical):
    return {
        "title": title,
        "start_date": start_date,
        "end_date": end_date or start_date,
        "start_time": start_time or None,
        "end_time": end_time or None,
        "notes": notes or None,
        "is_critical": int(bool(is_critical)),
    }


class Database:
    def __init__(self, db_path: str) -> None:
        self.connection = database(db_path)
        self.ingredients = self.connection.create(
            Ingredient, name="ingredients", pk="id", transform=True
        )
        self.ingredients.create_index(["name"], unique=True, if_not_exists=True)
        self.recipes = self.connection.create(Recipe, name="recipes", pk="id", transform=True)
        self.recipe_ingredients = self.connection.create(
            RecipeIngredient, name="recipe_ingredients", pk="id", transform=True
        )
        self.recipe_ingredients.create_index(
            ["recipe_id", "ingredient_id"], unique=True, if_not_exists=True
        )
        self.calendar_events = self.connection.create(
            CalendarEvent, name="calendar_events", pk="id", transform=True
        )
        self.recurring_events = self.connection.create(
            RecurringEvent, name="recurring_events", pk="id", transform=True
        )

    def filtered_recipes(
        self,
        name: str | None = None,
        ingredient_id: int | None = None,
        servings: int | None = None,
        excluded_ingredient_ids: tuple[int, ...] = (),
    ) -> list[Recipe]:
        clauses: list[str] = []
        params: dict = {}
        if name:
            clauses.append("name LIKE :name_pattern")
            params["name_pattern"] = f"%{name}%"
        if servings:
            clauses.append("servings = :servings")
            params["servings"] = servings
        if ingredient_id:
            clauses.append(
                "id IN (SELECT recipe_id FROM recipe_ingredients WHERE ingredient_id = :ingredient_id)"
            )
            params["ingredient_id"] = ingredient_id
        if excluded_ingredient_ids:
            placeholders = ",".join(f":excl_{i}" for i in range(len(excluded_ingredient_ids)))
            clauses.append(
                f"id NOT IN (SELECT recipe_id FROM recipe_ingredients "
                f"WHERE ingredient_id IN ({placeholders}))"
            )
            params.update({f"excl_{i}": value for i, value in enumerate(excluded_ingredient_ids)})
        where_sql = " AND ".join(clauses) if clauses else "1=1"
        rows = self.connection.q(f"SELECT * FROM recipes WHERE {where_sql} ORDER BY name", params)
        return [Recipe(**row) for row in rows]

    def list_events_in_range(
        self, range_start: str, range_end: str, owner_id: str | None = None
    ) -> list[CalendarEvent]:
        "Events whose [start_date, end_date] overlaps [range_start, range_end], inclusive."
        clauses = ["start_date <= :range_end", "end_date >= :range_start"]
        params = {"range_start": range_start, "range_end": range_end}
        if owner_id:
            clauses.append("owner_id = :owner_id")
            params["owner_id"] = owner_id
        where_sql = " AND ".join(clauses)
        rows = self.connection.q(
            f"SELECT * FROM calendar_events WHERE {where_sql} ORDER BY start_date, start_time", params
        )
        return [CalendarEvent(**row) for row in rows]

    def add_event(
        self,
        owner_id: str,
        title: str,
        start_date: str,
        end_date: str,
        start_time: str,
        end_time: str,
        notes: str,
        is_critical: bool,
    ) -> CalendarEvent:
        fields = _normalize_event_fields(title, start_date, end_date, start_time, end_time, notes, is_critical)
        return self.calendar_events.insert(CalendarEvent(owner_id=owner_id, **fields))

    def update_event(
        self,
        event_id: int,
        title: str,
        start_date: str,
        end_date: str,
        start_time: str,
        end_time: str,
        notes: str,
        is_critical: bool,
    ) -> CalendarEvent:
        fields = _normalize_event_fields(title, start_date, end_date, start_time, end_time, notes, is_critical)
        return self.calendar_events.update({"id": event_id, **fields})

    def list_recurring_events(self) -> list[RecurringEvent]:
        return self.recurring_events(order_by="month, day")

    def add_recurring_event(self, title: str, month: int, day: int) -> RecurringEvent:
        return self.recurring_events.insert(
            RecurringEvent(
                title=title, month=month, day=day, created_at=datetime.now(timezone.utc).isoformat()
            )
        )

    def update_recurring_event(self, event_id: int, title: str, month: int, day: int) -> RecurringEvent:
        return self.recurring_events.update({"id": event_id, "title": title, "month": month, "day": day})


site_db = Database(SiteConfig().db_path)
