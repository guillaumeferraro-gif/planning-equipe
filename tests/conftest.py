from datetime import date
import pytest
from planning.domain import new_state

@pytest.fixture
def state():
    value = new_state(2026)
    value["settings"]["rest_clock"] = "elapsed"
    for nurse in value["nurses"]:
        nurse["contracts"] = [{"from": "1900-01-01", "percent": 100}]
    return value

def assign(state, day, nurse, shift, **flags):
    state["assignments"].setdefault(day, {})[nurse] = {
        "shift": shift, "locked": False, "confirmed": False, **flags
    }
