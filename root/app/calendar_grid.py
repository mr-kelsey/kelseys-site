"""Presentation-generic month-grid rendering for the admin calendar. Named for what it
actually contains (month-grid rendering), not "calendar_shared" -- that name made sense in
the project this was ported from, which had two calendars sharing it; here there's only one.
"""

import calendar as cal
from datetime import date, timedelta

from fasthtml import common as Fast

WEEKDAY_LABELS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]


def parse_date(value):
    "Returns a date, or None for a blank/malformed value -- callers treat None as 'invalid'."
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def parse_int_or(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def month_grid(year, month):
    return cal.Calendar(firstweekday=6).monthdatescalendar(year, month)


def events_by_date(events, grid_start, grid_end):
    "Buckets events whose [start_date, end_date] spans days into a dict keyed by each spanned date."
    by_date = {}
    for event in events:
        event_start = max(date.fromisoformat(event.start_date), grid_start)
        event_end = min(date.fromisoformat(event.end_date), grid_end)
        current = event_start
        while current <= event_end:
            by_date.setdefault(current, []).append(event)
            current += timedelta(days=1)
    return by_date


def month_nav(year, month, url_fn):
    "url_fn(year, month) builds the link for that month; the caller owns any extra filter state."
    prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
    next_year, next_month = (year + 1, 1) if month == 12 else (year, month + 1)
    today = date.today()
    return Fast.Div(
        Fast.A("< Prev", href=url_fn(prev_year, prev_month)),
        Fast.Span(f"{cal.month_name[month]} {year}", cls="month-label"),
        Fast.A("Next >", href=url_fn(next_year, next_month)),
        Fast.A("Today", href=url_fn(today.year, today.month)),
        cls="month-nav",
    )


def day_square(day_date, in_current_month, is_today, badges, day_url, extra_classes=(), critical=False):
    """badges is a list of pre-rendered Fast.Div elements; day_url is the hx-get target for that day's
    dialog. critical is a generic "this day needs to visually stand out" flag for a caller to set when
    any event landing on this day is significant enough that it shouldn't blend into a busy month."""
    classes = ["day-square", *extra_classes]
    if not in_current_month:
        classes.append("outside-month")
    if is_today:
        classes.append("today")
    if critical:
        classes.append("critical-day")
    return Fast.Div(
        Fast.Div(str(day_date.day), cls="day-number"),
        *badges,
        cls=" ".join(classes),
        hx_get=day_url,
        hx_target="#event-dialog-body",
        hx_swap="innerHTML",
        **{"hx-on::after-request": "document.getElementById('event-dialog').showModal()"},
    )


def calendar_grid(weeks, month, today, day_square_fn):
    "day_square_fn(day_date, in_current_month, is_today) -> a rendered day square."
    cells = [Fast.Div(label, cls="calendar-weekday") for label in WEEKDAY_LABELS]
    for week in weeks:
        for day_date in week:
            cells.append(day_square_fn(day_date, day_date.month == month, day_date == today))
    return Fast.Div(*cells, cls="calendar-grid")
