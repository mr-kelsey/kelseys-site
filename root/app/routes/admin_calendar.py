import calendar as cal
from datetime import date
from urllib.parse import urlencode

from fastlite import NotFoundError
from fasthtml import common as Fast

from app.auth import admin_layout, require_admin
from app.calendar_grid import (
    calendar_grid,
    day_square,
    events_by_date,
    month_grid,
    month_nav,
    parse_date,
    parse_int_or,
)
from app.db import site_db
from app.family import FAMILY_MEMBERS, get_member

router = Fast.APIRouter()


def _calendar_url(year, month, member_id=None, base="/admin/calendar"):
    params = {"year": year, "month": month}
    if member_id:
        params["member_id"] = member_id
    return f"{base}?{urlencode(params)}"


def _is_checkbox_checked(value):
    return value in ("1", "true", "on")


def _validate_event_dates(title, start_date, end_date):
    "Returns (title, start_date, end_date, start_date_parsed, error) -- error is None on success."
    title = title.strip()
    start_date = start_date.strip()
    end_date = end_date.strip()
    if not title or not start_date:
        return title, start_date, end_date, None, "Title and start date are required."
    start_date_parsed = parse_date(start_date)
    if start_date_parsed is None:
        return title, start_date, end_date, None, "Invalid start date."
    if end_date:
        end_date_parsed = parse_date(end_date)
        if end_date_parsed is None:
            return title, start_date, end_date, start_date_parsed, "Invalid end date."
        if end_date_parsed < start_date_parsed:
            return title, start_date, end_date, start_date_parsed, "End date cannot be before start date."
    return title, start_date, end_date, start_date_parsed, None


def _recurring_events_by_date(recurring_events, weeks):
    by_date = {}
    for week in weeks:
        for day_date in week:
            matches = [
                recurring_event
                for recurring_event in recurring_events
                if recurring_event.month == day_date.month and recurring_event.day == day_date.day
            ]
            if matches:
                by_date[day_date] = matches
    return by_date


def _event_bar(event):
    member = get_member(event.owner_id)
    color = member["color"] if member else "#999999"
    return Fast.Div(cls="event-bar", style=f"background-color: {color}", title=event.title)


def _recurring_label(recurring_event):
    return Fast.Div(recurring_event.title, cls="recurring-label")


def _family_day_square(day_date, in_current_month, is_today, events_for_day, recurring_for_day, year, month, member_id):
    badges = [
        Fast.Div(*[_event_bar(event) for event in events_for_day], cls="event-bars"),
        Fast.Div(*[_recurring_label(r) for r in recurring_for_day], cls="recurring-labels"),
    ]
    critical = any(event.is_critical for event in events_for_day)
    day_url = _calendar_url(year, month, member_id, base=f"/admin/calendar/day/{day_date.isoformat()}")
    return day_square(day_date, in_current_month, is_today, badges, day_url, critical=critical)


def _admin_calendar_grid(weeks, month, events_map, recurring_by_date, today, year, member_id):
    return calendar_grid(
        weeks,
        month,
        today,
        lambda day_date, in_current_month, is_today: _family_day_square(
            day_date,
            in_current_month,
            is_today,
            events_map.get(day_date, []),
            recurring_by_date.get(day_date, []),
            year,
            month,
            member_id,
        ),
    )


def _month_nav(year, month, member_id):
    return month_nav(year, month, lambda nav_year, nav_month: _calendar_url(nav_year, nav_month, member_id))


def _filter_row(year, month, member_id):
    def link(label, target_member_id, is_active):
        href = _calendar_url(year, month, target_member_id) if target_member_id else _calendar_url(year, month)
        return Fast.A(label, href=href, cls="active" if is_active else "")

    links = [link("Everyone", None, member_id is None)]
    links += [link(member["name"], member["id"], member_id == member["id"]) for member in FAMILY_MEMBERS]
    return Fast.Div(*links, cls="filter-row")


def _event_dialog():
    return Fast.Dialog(Fast.Div(id="event-dialog-body"), id="event-dialog")


def _show_form_js(form_id):
    return (
        "document.querySelectorAll('#event-dialog-body .event-form').forEach(f => f.hidden = true); "
        f"document.getElementById('{form_id}').hidden = false;"
    )


def _event_form(
    form_id, action, submit_label, event=None, default_date="", year="", month="", member_id="", hidden=True
):
    return Fast.Form(
        Fast.Input(name="title", placeholder="Title", value=event.title if event else "", required=True),
        Fast.Input(
            name="start_date",
            type="date",
            value=event.start_date if event else default_date,
            required=True,
        ),
        Fast.Input(name="end_date", type="date", value=event.end_date if event else ""),
        Fast.Input(name="start_time", type="time", value=(event.start_time or "") if event else ""),
        Fast.Input(name="end_time", type="time", value=(event.end_time or "") if event else ""),
        Fast.Textarea(event.notes or "" if event else "", name="notes", placeholder="Notes (optional)"),
        Fast.Label(
            Fast.Input(
                name="is_critical",
                type="checkbox",
                value="1",
                checked=bool(event.is_critical) if event else False,
            ),
            " Can't miss",
        ),
        Fast.Input(type="hidden", name="redirect_year", value=str(year)),
        Fast.Input(type="hidden", name="redirect_month", value=str(month)),
        Fast.Input(type="hidden", name="redirect_member_id", value=member_id or ""),
        Fast.Button(submit_label, type="submit"),
        method="post",
        action=action,
        id=form_id,
        cls="event-form",
        hidden=hidden,
    )


def _validate_recurring_event(title, month, day):
    "Returns (title, month, day, error) -- validated against a leap year so Feb 29 is allowed."
    title = title.strip()
    if not title:
        return title, month, day, "Title is required."
    try:
        month, day = int(month), int(day)
        date(2000, month, day)
    except (TypeError, ValueError):
        return title, month, day, "Invalid month/day."
    return title, month, day, None


def _month_select(selected_month=None):
    return Fast.Select(
        *[
            Fast.Option(cal.month_name[month], value=str(month), selected=(month == selected_month))
            for month in range(1, 13)
        ],
        name="month",
        required=True,
    )


def _recurring_event_form(action, submit_label, recurring_event=None, error=None):
    return Fast.Form(
        Fast.P(error, cls="error") if error else None,
        Fast.Input(
            name="title", placeholder="Title", value=recurring_event.title if recurring_event else "", required=True
        ),
        _month_select(recurring_event.month if recurring_event else None),
        Fast.Input(
            name="day",
            placeholder="day",
            type="number",
            min="1",
            max="31",
            value=recurring_event.day if recurring_event else "",
            required=True,
        ),
        Fast.Button(submit_label, type="submit"),
        method="post",
        action=action,
    )


def _recurring_event_row(recurring_event):
    return Fast.Li(
        _recurring_event_form(
            action=f"/admin/calendar/recurring/{recurring_event.id}/edit",
            submit_label="Save",
            recurring_event=recurring_event,
        ),
        Fast.Form(
            Fast.Button("Delete", type="submit"),
            method="post",
            action=f"/admin/calendar/recurring/{recurring_event.id}/delete",
        ),
        cls="recurring-event-row",
    )


def _delete_event_form(event_id, year, month, member_id):
    return Fast.Form(
        Fast.Input(type="hidden", name="redirect_year", value=str(year)),
        Fast.Input(type="hidden", name="redirect_month", value=str(month)),
        Fast.Input(type="hidden", name="redirect_member_id", value=member_id or ""),
        Fast.Button("Delete", type="submit"),
        method="post",
        action=f"/admin/calendar/{event_id}/delete",
    )


def _render_calendar_page(session, year, month, member_id, error=None):
    today = date.today()
    weeks = month_grid(year, month)
    grid_start, grid_end = weeks[0][0], weeks[-1][-1]
    events = site_db.list_events_in_range(grid_start.isoformat(), grid_end.isoformat(), owner_id=member_id or None)
    events_map = events_by_date(events, grid_start, grid_end)
    recurring_by_date = _recurring_events_by_date(site_db.list_recurring_events(), weeks)
    return admin_layout(
        "Calendar",
        Fast.H1("Family Calendar"),
        Fast.P(error, cls="error") if error else None,
        _month_nav(year, month, member_id),
        _filter_row(year, month, member_id),
        Fast.A("Manage yearly events", href="/admin/calendar/recurring", cls="manage-recurring-link"),
        _admin_calendar_grid(weeks, month, events_map, recurring_by_date, today, year, member_id),
        _event_dialog(),
    )


@router("/admin/calendar")
def get(session, year: int = None, month: int = None, member_id: str = None):
    if (redirect := require_admin(session)) is not None:
        return redirect
    if member_id and get_member(member_id) is not None:
        session["member_id"] = member_id
    today = date.today()
    year = year or today.year
    month = month or today.month
    return _render_calendar_page(session, year, month, member_id)


@router("/admin/calendar/day/{event_date}")
def get(session, event_date: str, year: int = None, month: int = None, member_id: str = None):
    if (redirect := require_admin(session)) is not None:
        return redirect
    day = parse_date(event_date)
    if day is None:
        return Fast.P("Invalid date.", cls="error")
    year = year or day.year
    month = month or day.month
    events = site_db.list_events_in_range(event_date, event_date, owner_id=member_id or None)
    rows = []
    edit_forms = []
    for event in events:
        member = get_member(event.owner_id)
        owner_name = member["name"] if member else event.owner_id
        edit_form_id = f"edit-event-form-{event.id}"
        actions = [
            Fast.Button("Edit", type="submit", onclick=_show_form_js(edit_form_id)),
            _delete_event_form(event.id, year, month, member_id),
        ]
        edit_forms.append(
            _event_form(
                form_id=edit_form_id,
                action=f"/admin/calendar/{event.id}/edit",
                submit_label="Save Changes",
                event=event,
                year=year,
                month=month,
                member_id=member_id,
            )
        )
        rows.append(Fast.Li(f"{event.title} — {owner_name}", *actions))
    return (
        Fast.H3(day.isoformat()),
        Fast.Ul(*rows) if rows else Fast.P("No events yet."),
        *edit_forms,
        Fast.Div(
            Fast.Button("Add Event", type="button", onclick=_show_form_js("add-event-form")),
            _event_form(
                form_id="add-event-form",
                action="/admin/calendar",
                submit_label="Add Event",
                default_date=event_date,
                year=year,
                month=month,
                member_id=member_id,
                hidden=bool(events),
            ),
        ),
        Fast.Button("Close", type="button", onclick="document.getElementById('event-dialog').close()"),
    )


@router("/admin/calendar")
def post(
    session,
    title: str,
    start_date: str,
    end_date: str = "",
    start_time: str = "",
    end_time: str = "",
    notes: str = "",
    is_critical: str = "",
    redirect_year: str = "",
    redirect_month: str = "",
    redirect_member_id: str = "",
):
    if (redirect := require_admin(session)) is not None:
        return redirect
    today = date.today()
    year = parse_int_or(redirect_year, today.year)
    month = parse_int_or(redirect_month, today.month)
    member_id = session.get("member_id")
    if member_id is None:
        return _render_calendar_page(
            session, year, month, redirect_member_id or None,
            error="Pick a family member from the filter before adding events.",
        )
    title, start_date, end_date, start_date_parsed, error = _validate_event_dates(title, start_date, end_date)
    if error is not None:
        return _render_calendar_page(session, year, month, redirect_member_id or None, error=error)
    site_db.add_event(
        owner_id=member_id,
        title=title,
        start_date=start_date,
        end_date=end_date or None,
        start_time=start_time.strip() or None,
        end_time=end_time.strip() or None,
        notes=notes.strip() or None,
        is_critical=_is_checkbox_checked(is_critical),
    )
    year = parse_int_or(redirect_year, start_date_parsed.year)
    month = parse_int_or(redirect_month, start_date_parsed.month)
    return Fast.Redirect(_calendar_url(year, month, redirect_member_id))


@router("/admin/calendar/{event_id}/delete")
def post(session, event_id: int, redirect_year: str = "", redirect_month: str = "", redirect_member_id: str = ""):
    if (redirect := require_admin(session)) is not None:
        return redirect
    try:
        site_db.calendar_events.get(event_id)
    except NotFoundError:
        return Fast.Redirect("/admin/calendar")
    site_db.calendar_events.delete(event_id)
    today = date.today()
    year = parse_int_or(redirect_year, today.year)
    month = parse_int_or(redirect_month, today.month)
    return Fast.Redirect(_calendar_url(year, month, redirect_member_id))


@router("/admin/calendar/{event_id}/edit")
def post(
    session,
    event_id: int,
    title: str,
    start_date: str,
    end_date: str = "",
    start_time: str = "",
    end_time: str = "",
    notes: str = "",
    is_critical: str = "",
    redirect_year: str = "",
    redirect_month: str = "",
    redirect_member_id: str = "",
):
    if (redirect := require_admin(session)) is not None:
        return redirect
    try:
        site_db.calendar_events.get(event_id)
    except NotFoundError:
        return Fast.Redirect("/admin/calendar")
    today = date.today()
    year = parse_int_or(redirect_year, today.year)
    month = parse_int_or(redirect_month, today.month)
    title, start_date, end_date, start_date_parsed, error = _validate_event_dates(title, start_date, end_date)
    if error is not None:
        return _render_calendar_page(session, year, month, redirect_member_id or None, error=error)
    site_db.update_event(
        event_id,
        title=title,
        start_date=start_date,
        end_date=end_date or None,
        start_time=start_time.strip() or None,
        end_time=end_time.strip() or None,
        notes=notes.strip() or None,
        is_critical=_is_checkbox_checked(is_critical),
    )
    year = parse_int_or(redirect_year, start_date_parsed.year)
    month = parse_int_or(redirect_month, start_date_parsed.month)
    return Fast.Redirect(_calendar_url(year, month, redirect_member_id))


@router("/admin/calendar/recurring")
def get(session):
    if (redirect := require_admin(session)) is not None:
        return redirect
    recurring_events = site_db.list_recurring_events()
    return admin_layout(
        "Yearly Events",
        Fast.H1("Yearly Events"),
        Fast.P("These repeat every year and are visible to everyone, regardless of the family member filter."),
        _recurring_event_form(action="/admin/calendar/recurring", submit_label="Add Yearly Event"),
        Fast.Ul(*[_recurring_event_row(r) for r in recurring_events])
        if recurring_events
        else Fast.P("No yearly events yet."),
        Fast.A("Back to calendar", href="/admin/calendar"),
    )


@router("/admin/calendar/recurring")
def post(session, title: str, month: str, day: str):
    if (redirect := require_admin(session)) is not None:
        return redirect
    title, month, day, error = _validate_recurring_event(title, month, day)
    if error is not None:
        return admin_layout(
            "Yearly Events",
            Fast.H1("Yearly Events"),
            _recurring_event_form(action="/admin/calendar/recurring", submit_label="Add Yearly Event", error=error),
            Fast.A("Back to calendar", href="/admin/calendar"),
        )
    site_db.add_recurring_event(title, month, day)
    return Fast.Redirect("/admin/calendar/recurring")


@router("/admin/calendar/recurring/{event_id}/edit")
def post(session, event_id: int, title: str, month: str, day: str):
    if (redirect := require_admin(session)) is not None:
        return redirect
    title, month, day, error = _validate_recurring_event(title, month, day)
    if error is not None:
        return Fast.Redirect("/admin/calendar/recurring")
    site_db.update_recurring_event(event_id, title, month, day)
    return Fast.Redirect("/admin/calendar/recurring")


@router("/admin/calendar/recurring/{event_id}/delete")
def post(session, event_id: int):
    if (redirect := require_admin(session)) is not None:
        return redirect
    site_db.recurring_events.delete(event_id)
    return Fast.Redirect("/admin/calendar/recurring")
