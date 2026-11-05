from starlette.testclient import TestClient

from app.db import Database
from app.family import FAMILY_MEMBERS

FIRST_MEMBER_ID = FAMILY_MEMBERS[0]["id"]
SECOND_MEMBER_ID = FAMILY_MEMBERS[1]["id"]


def _pick_member(client: TestClient, member_id: str) -> None:
    client.get("/admin/calendar", params={"member_id": member_id})


def test_get_admin_calendar_redirects_when_not_authenticated(client: TestClient) -> None:
    response = client.get("/admin/calendar", follow_redirects=False)
    assert response.headers["location"] == "/admin/login"


def test_get_admin_calendar_returns_200_when_authenticated(admin_client: TestClient) -> None:
    response = admin_client.get("/admin/calendar")
    assert response.status_code == 200


def test_post_admin_calendar_add_event_requires_a_member_selected(
    admin_client: TestClient, db: Database
) -> None:
    admin_client.post("/admin/calendar", data={"title": "Dentist", "start_date": "2026-05-01"})
    assert db.calendar_events.count == 0


def test_post_admin_calendar_add_event_creates_event(admin_client: TestClient, db: Database) -> None:
    _pick_member(admin_client, FIRST_MEMBER_ID)
    admin_client.post(
        "/admin/calendar",
        data={"title": "Dentist", "start_date": "2026-05-01", "member_id": FIRST_MEMBER_ID},
    )
    assert db.calendar_events.count == 1


def test_post_admin_calendar_add_event_rejects_missing_title(
    admin_client: TestClient, db: Database
) -> None:
    _pick_member(admin_client, FIRST_MEMBER_ID)
    admin_client.post("/admin/calendar", data={"title": "", "start_date": "2026-05-01"})
    assert db.calendar_events.count == 0


def test_post_admin_calendar_edit_event_allowed_for_any_owner(
    admin_client: TestClient, db: Database
) -> None:
    "The ownership-simplification regression test: one shared admin login can edit any member's event."
    _pick_member(admin_client, FIRST_MEMBER_ID)
    admin_client.post(
        "/admin/calendar",
        data={"title": "Dentist", "start_date": "2026-05-01", "member_id": FIRST_MEMBER_ID},
    )
    event_id = db.calendar_events(order_by="id")[0].id
    _pick_member(admin_client, SECOND_MEMBER_ID)
    admin_client.post(
        f"/admin/calendar/{event_id}/edit",
        data={"title": "Dentist (rescheduled)", "start_date": "2026-05-02"},
    )
    assert db.calendar_events.get(event_id).title == "Dentist (rescheduled)"


def test_post_admin_calendar_delete_event_allowed_for_any_owner(
    admin_client: TestClient, db: Database
) -> None:
    "The ownership-simplification regression test: one shared admin login can delete any member's event."
    _pick_member(admin_client, FIRST_MEMBER_ID)
    admin_client.post(
        "/admin/calendar",
        data={"title": "Dentist", "start_date": "2026-05-01", "member_id": FIRST_MEMBER_ID},
    )
    event_id = db.calendar_events(order_by="id")[0].id
    _pick_member(admin_client, SECOND_MEMBER_ID)
    admin_client.post(f"/admin/calendar/{event_id}/delete")
    assert db.calendar_events.count == 0


def test_get_admin_calendar_recurring_lists_yearly_events(
    admin_client: TestClient, db: Database
) -> None:
    db.add_recurring_event("Anniversary", 6, 15)
    response = admin_client.get("/admin/calendar/recurring")
    assert "Anniversary" in response.text


def test_post_admin_calendar_recurring_adds_yearly_event(
    admin_client: TestClient, db: Database
) -> None:
    admin_client.post("/admin/calendar/recurring", data={"title": "Anniversary", "month": "6", "day": "15"})
    assert db.recurring_events.count == 1


def test_post_admin_calendar_recurring_rejects_invalid_day(
    admin_client: TestClient, db: Database
) -> None:
    admin_client.post("/admin/calendar/recurring", data={"title": "Bad Day", "month": "2", "day": "31"})
    assert db.recurring_events.count == 0
