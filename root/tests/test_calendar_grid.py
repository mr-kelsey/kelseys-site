from datetime import date

from app.calendar_grid import day_square, parse_date, parse_int_or


def test_parse_date_returns_date_for_a_valid_iso_string():
    assert parse_date("2026-04-01") == date(2026, 4, 1)


def test_parse_date_returns_none_for_a_malformed_string():
    assert parse_date("not-a-date") is None


def test_parse_date_returns_none_for_none_instead_of_raising():
    assert parse_date(None) is None


def test_parse_date_returns_none_for_an_empty_string():
    assert parse_date("") is None


def test_parse_int_or_returns_parsed_int():
    assert parse_int_or("5", 0) == 5


def test_parse_int_or_returns_default_for_none():
    assert parse_int_or(None, 3) == 3


def test_parse_int_or_returns_default_for_a_malformed_string():
    assert parse_int_or("not-a-number", 3) == 3


def _classes(critical=False, extra_classes=()):
    rendered = day_square(
        date(2026, 4, 1), True, False, [], "/day-url", extra_classes=extra_classes, critical=critical
    )
    return rendered.attrs["class"]


def test_day_square_has_no_critical_day_class_by_default():
    assert "critical-day" not in _classes().split()


def test_day_square_has_critical_day_class_when_flagged():
    assert "critical-day" in _classes(critical=True).split()


def test_day_square_keeps_extra_classes_alongside_critical_day():
    classes = _classes(critical=True, extra_classes=("some-other-class",)).split()
    assert "some-other-class" in classes and "critical-day" in classes
