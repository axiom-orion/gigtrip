"""Itinerary-optimisation ablation: greedy baselines vs. the exact optimum.

For each scenario it plans a trip with each rung (sort-by-date -> prize-greedy ->
distance-aware -> optimal) and reports the preference-weighted **value captured**, the
**travel kilometres**, and **value per 1,000 km**. The headline is the optimiser's *lift*
over the sort-by-date baseline at the same budget. Numbers are produced here, not asserted.

Run: python eval/run_eval.py
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # the result table uses ↑/↓/→ (utf-8 on Windows)

from gigtrip import PLANNERS, Constraints, load_corpus  # noqa: E402

SCENARIOS = ROOT / "eval" / "scenarios.json"


def _constraints(s: dict) -> Constraints:
    return Constraints(
        home_name=s["home"]["name"], home_lat=s["home"]["lat"], home_lon=s["home"]["lon"],
        start=date.fromisoformat(s["start"]), end=date.fromisoformat(s["end"]),
        max_travel_km=float(s["max_travel_km"]), max_events=s.get("max_events"),
        max_km_per_day=float(s.get("max_km_per_day", 1200)), default_pref=0.0)


def _vpk(value: float, km: float) -> float:
    return value / (km / 1000.0) if km > 1e-9 else 0.0


def main() -> None:
    events = load_corpus()
    scenarios = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    rows: list[dict] = []
    md = ["# gigtrip — itinerary optimisation eval\n",
          f"{len(events)} synthetic events · {len(scenarios)} scenarios · "
          "value = sum of preference weights · travel = round-trip haversine km.\n"]

    lifts = []
    for s in scenarios:
        c = _constraints(s)
        prefs = {k.lower(): float(v) for k, v in s["prefs"].items()}
        md += [f"\n## {s['name']}",
               f"home **{c.home_name}** · {c.start}→{c.end} · budget "
               f"{c.max_travel_km:.0f} km · ≤{c.max_events} events\n",
               "| planner | events | value ↑ | travel km ↓ | value/1000km ↑ |",
               "|---|--:|--:|--:|--:|"]
        base_value = None
        for name, fn in PLANNERS.items():
            it = fn(events, prefs, c)
            if name == "by-date":
                base_value = it.value
            star = " **" if name == "optimal" else " "
            md.append(f"|{star}{name}{star.strip()} | {it.count} | {it.value:.0f} | "
                      f"{it.travel_km:.0f} | {_vpk(it.value, it.travel_km):.2f} |")
            rows.append({"scenario": s["name"], "planner": name, "events": it.count,
                         "value": it.value, "travel_km": round(it.travel_km, 1),
                         "itinerary": list(it.ids())})
        opt_value = rows[-1]["value"]
        if base_value and base_value > 0:
            lift = 100.0 * (opt_value - base_value) / base_value
            lifts.append(lift)
            md.append(f"\n_optimal captures **{lift:+.0f}%** value vs. sort-by-date, same budget._")

    avg = sum(lifts) / len(lifts) if lifts else 0.0
    md.insert(2, f"\n**Headline:** across {len(scenarios)} scenarios the exact optimiser captures "
                 f"**{avg:+.0f}%** more preference-weighted value than the sort-by-date baseline "
                 f"at the same travel budget.\n")
    md += ["\n---\n",
           "**Honest scope.** Travel cost is straight-line haversine km, not road/airfare "
           "routing (monotonic in real cost, which is what the selection needs). The corpus "
           "is synthetic and deterministic; live Bandsintown data is an optional front door. "
           "The optimiser is exact (Pareto label-setting), verified against brute force in "
           "`tests/`."]

    (ROOT / "eval" / "results.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (ROOT / "eval" / "results.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
    print("\n".join(md))
    print("\nwrote eval/results.md and eval/results.json", file=sys.stderr)


if __name__ == "__main__":
    main()
