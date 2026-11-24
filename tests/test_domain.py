from datetime import date, datetime
from zoneinfo import ZoneInfo
import copy
import pytest
from planning.domain import (
    DomainError, annual_totals, change_tiih, new_state, parse_duration,
    set_absence, shift_interval, tiih_required, validate_schedule, validate_state,
)
from conftest import assign

TZ = ZoneInfo("Europe/Paris")

def test_absence_friday_monday_and_custom_credit(state):
    set_absence(state, "ide-a", datetime(2026, 11, 20, tzinfo=TZ),
                datetime(2026, 11, 24, tzinfo=TZ), "Maladie")
    assert sum(state["absences"][0]["credits"].values()) == 924
    assert state["absences"][0]["end"].startswith("2026-11-24")
    set_absence(state, "ide-b", datetime(2026, 11, 23, 9, tzinfo=TZ),
                datetime(2026, 11, 23, 11, tzinfo=TZ), "Formation",
                credits={"2026-11-23": 120})
    assert annual_totals(state, 2026)[1]["absence_minutes"] == 120

def test_absence_overlap_rejected_atomically(state):
    start, end = datetime(2026, 11, 20, tzinfo=TZ), datetime(2026, 11, 24, tzinfo=TZ)
    set_absence(state, "ide-a", start, end, "Maladie")
    before = copy.deepcopy(state)
    with pytest.raises(DomainError):
        set_absence(state, "ide-a", start, end, "RTT")
    assert state == before

def test_night_tiih_and_cross_month_series(state):
    assign(state, "2026-11-30", "ide-a", "N")
    assign(state, "2026-12-01", "ide-a", "T")
    issues = validate_schedule(state, date(2026, 12, 1), date(2026, 12, 2), coverage=False)
    assert any(i.code == "rest" for i in issues)
    for day in ["2026-11-28", "2026-11-29", "2026-11-30", "2026-12-01"]:
        assign(state, day, "ide-b", "J")
    assert any(i.code == "consecutive" for i in validate_schedule(
        state, date(2026, 12, 1), date(2026, 12, 2), coverage=False))

def test_rolling_hours_finds_intraday_window(state):
    # Every seven-date window has at most48h by start dates, yet an intraday
    #168h window contains60h including the overnight start on the first day.
    assign(state, "2026-11-01", "ide-a", "N")
    for day in ["2026-11-03", "2026-11-04", "2026-11-06", "2026-11-08"]:
        assign(state, day, "ide-a", "J")
    assert any(i.code == "weekly" for i in validate_schedule(
        state, date(2026, 11, 2), date(2026, 11, 8), coverage=False))

def test_weekend_pair_and_monday(state):
    assign(state, "2026-11-21", "ide-a", "J")
    assert any(i.code == "weekend" for i in validate_schedule(
        state, date(2026, 11, 21), date(2026, 11, 23), coverage=False))
    assign(state, "2026-11-22", "ide-a", "J")
    assign(state, "2026-11-23", "ide-a", "J")
    assert any(i.code == "monday" for i in validate_schedule(
        state, date(2026, 11, 21), date(2026, 11, 23), coverage=False))

def test_tiih_move_restore_collision_and_confirmed(state):
    origin, dest = date(2026, 11, 24), date(2026, 11, 25)
    assign(state, str(origin), "ide-a", "T")
    change_tiih(state, origin, dest)
    assert not tiih_required(state, origin) and tiih_required(state, dest)
    assert "ide-a" not in state["assignments"].get(str(origin), {})
    with pytest.raises(DomainError):
        change_tiih(state, date(2026, 11, 26), dest)
    change_tiih(state, origin, restore=True)
    assert tiih_required(state, origin) and not tiih_required(state, dest)
    with pytest.raises(DomainError):
        change_tiih(state, origin, date(2026, 12, 25))
    assign(state, str(origin), "ide-a", "T", confirmed=True)
    with pytest.raises(DomainError):
        change_tiih(state, origin, None)

def test_counters_filter_year_oat_optional_and_quotas(state):
    assign(state, "2025-12-31", "ide-a", "N")
    assign(state, "2026-11-24", "ide-a", "T")
    row = annual_totals(state, 2026)[0]
    assert row["planned_minutes"] == 462 and row["target_minutes"] is None
    state["oat"]["2026"] = 60000
    state["nurses"][0]["contracts"] = [{"from": "1900-01-01", "percent": 80}]
    assert annual_totals(state, 2026)[0]["target_minutes"] == 48000
    state["nurses"][0]["contracts"] = [{"from": "2026-07-01", "percent": 80}]
    assert annual_totals(state, 2026)[0]["target_minutes"] is None
    state["nurses"][0]["contracts"].insert(0,{"from":"2026-01-01","percent":100})
    assert annual_totals(state,2026)[0]["target_minutes"] == round(60000*(181*100+184*80)/36500)

def test_confirmed_not_double_counted_and_absence_conflict(state):
    assign(state, "2026-11-24", "ide-a", "J", confirmed=True)
    row = annual_totals(state, 2026)[0]
    assert row["confirmed_minutes"] == 720 and row["planned_minutes"] == 0
    set_absence(state, "ide-a", datetime(2026, 11, 24, tzinfo=TZ),
                datetime(2026, 11, 25, tzinfo=TZ), "Maladie")
    row = annual_totals(state, 2026)[0]
    assert row["conflicts"] == 1 and row["total_minutes"] is None

def test_dst_elapsed_and_displayed_rest_are_explicit(state):
    assign(state, "2027-03-27", "ide-a", "J")
    assign(state, "2027-03-28", "ide-a", "J")
    issues = validate_schedule(state, date(2027, 3, 27), date(2027, 3, 28), coverage=False)
    assert any(i.code == "rest" for i in issues)
    state["settings"]["rest_clock"] = "wall"
    assert not any(i.code == "rest" for i in validate_schedule(
        state, date(2027, 3, 27), date(2027, 3, 28), coverage=False))
    a, b = shift_interval(date(2026, 10, 24), "N")
    assert b-a == 13*60

def test_unknown_history_and_quotas_not_silently_complete():
    state = new_state(2026)
    state["settings"]["rest_clock"] = None
    assert sum(n["contracts"][0]["percent"] is None for n in state["nurses"]) == 4
    codes = {i.code for i in validate_schedule(state, date(2026, 11, 1), date(2026, 11, 30))}
    assert {"history", "rest_convention", "quota"}.issubset(codes)

def test_duration_validation_and_structure(state):
    assert parse_duration("7:42") == 462
    with pytest.raises(DomainError):
        parse_duration("7:70")
    state["nurses"][0]["contracts"][0]["percent"] = 0
    with pytest.raises(DomainError):
        validate_state(state)
