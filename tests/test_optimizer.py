"""Optimizer correctness + property tests.

The load-bearing test (`test_optimal_matches_brute_force`) proves the exact Pareto
label-setting optimiser returns the true optimum by comparing it to a brute-force oracle on
random small instances. The rest check feasibility, baseline ordering, and budget monotonicity.
"""
from __future__ import annotations

import json
import random
from datetime import date, timedelta
from pathlib import Path

import pytest

from gigtrip import (
    PLANNERS,
    Constraints,
    Event,
    brute_force_optimal,
    candidates,
    load_corpus,
    plan_optimal,
    prize,
    route_km,
)
from gigtrip.optimizer import _legs_feasible, feasible_leg

ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = json.loads((ROOT / "eval" / "scenarios.json").read_text(encoding="utf-8"))


def _constraints(s: dict) -> Constraints:
    return Constraints(
        home_name=s["home"]["name"], home_lat=s["home"]["lat"], home_lon=s["home"]["lon"],
        start=date.fromisoformat(s["start"]), end=date.fromisoformat(s["end"]),
        max_travel_km=float(s["max_travel_km"]), max_events=s.get("max_events"),
        max_km_per_day=float(s.get("max_km_per_day", 1200)))


def _prefs(s: dict) -> dict[str, float]:
    return {k.lower(): float(v) for k, v in s["prefs"].items()}


def _feasible(it, c, prefs) -> bool:
    if c.max_events is not None and it.count > c.max_events:
        return False
    if not _legs_feasible(it.events, c):
        return False
    if it.travel_km > c.max_travel_km + 1e-6:
        return False
    # value is internally consistent
    return abs(it.value - sum(prize(e, prefs, c.default_pref) for e in it.events)) < 1e-9


# --------------------------- units ----------------------------------------- #
def test_corpus_loads():
    events = load_corpus()
    assert len(events) > 20
    assert all(e.lat != 0 and e.lon != 0 for e in events)
    assert {e.kind for e in events} <= {"music", "sports", "comedy"}


def test_haversine_and_feasibility():
    sd = Event("a", "X", "music", date(2026, 5, 1), "San Diego", "v", 32.72, -117.16)
    la = Event("b", "Y", "music", date(2026, 5, 1), "Los Angeles", "v", 34.05, -118.24)
    c = Constraints("H", 32.7, -117.1, date(2026, 5, 1), date(2026, 6, 1), 99999)
    # SD<->LA same day is far enough apart that it's a same-day distinct-city violation
    assert not feasible_leg(sd, la, c)              # ~180 km, same day -> infeasible (>50 km)
    la2 = Event("b2", "Y", "music", date(2026, 5, 3), "Los Angeles", "v", 34.05, -118.24)
    assert feasible_leg(sd, la2, c)                 # two days later -> fine
    far2 = Event("c2", "Z", "music", date(2026, 5, 2), "Boston", "v", 42.36, -71.06)
    assert not feasible_leg(sd, far2, c)            # ~4500 km in 1 day -> infeasible


# --------------------------- correctness oracle ---------------------------- #
def _random_instance(rng: random.Random):
    n = rng.randint(5, 11)
    base = date(2026, 5, 1)
    titles = ["a", "b", "c", "d", "e"]
    events = []
    for i in range(n):
        events.append(Event(
            id=f"e{i}", title=rng.choice(titles), kind="music",
            day=base + timedelta(days=rng.randint(0, 40)),
            city="c", venue="v", lat=rng.uniform(25, 48), lon=rng.uniform(-123, -71)))
    prefs = {t: float(rng.randint(0, 3)) for t in titles}
    c = Constraints(
        "H", rng.uniform(25, 48), rng.uniform(-123, -71), base, base + timedelta(days=40),
        max_travel_km=rng.uniform(1500, 14000),
        max_events=rng.choice([None, 2, 3, 4]),
        max_km_per_day=rng.choice([800.0, 1200.0, 2500.0]))
    return events, prefs, c


@pytest.mark.parametrize("seed", range(40))
def test_optimal_matches_brute_force(seed):
    rng = random.Random(1000 + seed)
    events, prefs, c = _random_instance(rng)
    opt = plan_optimal(events, prefs, c)
    truth = brute_force_optimal(events, prefs, c)
    assert opt.value == pytest.approx(truth.value), f"seed {seed}: {opt.value} != {truth.value}"
    assert _feasible(opt, c, prefs)
    assert opt.travel_km <= c.max_travel_km + 1e-6


# --------------------------- scenario properties --------------------------- #
@pytest.mark.parametrize("s", SCENARIOS, ids=[s["name"] for s in SCENARIOS])
def test_optimal_beats_baselines_and_is_feasible(s):
    events, c, prefs = load_corpus(), _constraints(s), _prefs(s)
    results = {name: fn(events, prefs, c) for name, fn in PLANNERS.items()}
    opt = results["optimal"]
    for name, it in results.items():
        assert _feasible(it, c, prefs), f"{name} produced an infeasible itinerary"
        assert opt.value >= it.value - 1e-9, f"optimal ({opt.value}) < {name} ({it.value})"


@pytest.mark.parametrize("s", SCENARIOS, ids=[s["name"] for s in SCENARIOS])
def test_value_monotonic_in_budget(s):
    events, prefs = load_corpus(), _prefs(s)
    base = _constraints(s)
    prev = -1.0
    for mult in (0.25, 0.5, 1.0, 2.0, 5.0):
        c = Constraints(base.home_name, base.home_lat, base.home_lon, base.start, base.end,
                        max_travel_km=base.max_travel_km * mult, max_events=base.max_events,
                        max_km_per_day=base.max_km_per_day)
        v = plan_optimal(events, prefs, c).value
        assert v >= prev - 1e-9, "more budget should never reduce optimal value"
        prev = v


def test_empty_window_is_empty_trip():
    events = load_corpus()
    c = Constraints("H", 28.5, -81.4, date(2030, 1, 1), date(2030, 1, 2), 99999)
    assert candidates(events, c) == []
    it = plan_optimal(events, {}, c)
    assert it.count == 0 and it.value == 0.0 and it.travel_km == 0.0


def test_route_km_roundtrip():
    events = candidates(load_corpus(),
                        Constraints("Denver", 39.74, -104.99, date(2026, 5, 15),
                                    date(2026, 5, 19), 99999))
    assert route_km([], Constraints("H", 0, 0, date(2026, 1, 1), date(2026, 1, 2), 1)) == 0.0
    if events:
        assert route_km(events[:1], Constraints("Denver", 39.74, -104.99, events[0].day,
                        events[0].day, 99999)) > 0.0
