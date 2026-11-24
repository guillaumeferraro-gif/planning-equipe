from datetime import date, datetime
from zoneinfo import ZoneInfo
from copy import deepcopy
from planning.domain import dates, set_absence, validate_schedule
from planning.solver import generate_schedule
from conftest import assign


def test_solver_preserves_locks_finds_month_and_carries_periods(state):
    state["settings"]["rest_clock"] = "wall"
    assign(state, "2026-11-03", "ide-a", "J", locked=True)
    assign(state, "2026-11-09", "ide-a", "-", locked=True)
    assign(state, "2026-11-10", "ide-a", "N", locked=True)
    assign(state, "2026-11-11", "ide-a", "-", locked=True)
    before = deepcopy(state)
    result = generate_schedule(state, 2026, 11, time_limit=12)
    assert state == before
    assert result.status in ("feasible", "optimal"), result.message
    candidate = result.candidate
    assert candidate["assignments"]["2026-11-03"]["ide-a"]["shift"] == "J"
    assert candidate["assignments"]["2026-11-03"]["ide-a"]["locked"]
    assert candidate["assignments"]["2026-11-10"]["ide-a"]["shift"] == "N"
    assert result.isolated_nights >= 1
    assert not [i for i in validate_schedule(candidate,date(2026,11,1),date(2026,11,30)) if i.severity=="error"]
    assert any(d.startswith("2026-12") for d in candidate["phases"])
    for nid in [n["id"] for n in candidate["nurses"]]:
        a=candidate["phases"]["2026-11-30"][nid]
        b=candidate["phases"]["2026-12-01"][nid]
        assert b["age"] == (1 if a["mode"]!=b["mode"] else a["age"]+1)


def test_solver_missing_quotas_and_absence_impossibility(state):
    state["nurses"][0]["contracts"][0]["percent"] = None
    assert generate_schedule(state,2026,11,time_limit=1).status == "invalid_input"
    state["nurses"][0]["contracts"][0]["percent"] = 100
    tz=ZoneInfo("Europe/Paris")
    for nurse in state["nurses"]:
        set_absence(state,nurse["id"],datetime(2026,11,1,tzinfo=tz),datetime(2026,12,1,tzinfo=tz),"Maladie")
    result=generate_schedule(state,2026,11,time_limit=1)
    assert result.status == "infeasible" and result.candidate is None


def test_solver_timeout_not_infeasibility(state):
    result=generate_schedule(state,2026,11,time_limit=0.00001)
    assert result.status == "unknown" and result.candidate is None
