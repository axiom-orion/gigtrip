"""gigtrip — itinerary optimisation for live-event road trips.

Plan the set of concerts / games / shows that maximises preference-weighted value within a
travel budget. The optimiser (`plan_optimal`) is exact and pure-Python; the `plan_by_*`
functions are the greedy baselines the eval measures it against.
"""
from .data import fetch_bandsintown, load_corpus
from .model import Constraints, Event, Itinerary, prize
from .optimizer import (
    PLANNERS,
    brute_force_optimal,
    candidates,
    evaluate,
    plan_by_date,
    plan_by_prize,
    plan_by_ratio,
    plan_optimal,
    route_km,
)

__all__ = [
    "Event", "Constraints", "Itinerary", "prize",
    "load_corpus", "fetch_bandsintown",
    "candidates", "evaluate", "route_km",
    "plan_by_date", "plan_by_prize", "plan_by_ratio", "plan_optimal",
    "brute_force_optimal", "PLANNERS",
]
