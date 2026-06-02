# gigtrip

[![ci](https://github.com/axiom-orion/gigtrip/actions/workflows/ci.yml/badge.svg)](https://github.com/axiom-orion/gigtrip/actions/workflows/ci.yml)

<!-- LIVE_URL_START -->
**Live demo:** _not yet deployed_ — see [Quickstart](#quickstart). The deployed Streamlit app plans real trips over a bundled synthetic event corpus (live Bandsintown data optional).
<!-- LIVE_URL_END -->

Plan a road trip around live events — concerts, games, comedy. You give it your bands and teams, a home base, a date window, and a travel budget; it returns the **set of shows that maximises preference-weighted value within that budget**.

It is built to make one point measurable: **planning a trip around live events is constrained optimisation, not a sort.** The obvious approaches — "take the soonest shows," "take your favourite artists first" — leave value on the table because they ignore that every extra show costs travel you can't get back. Across a fixed set of scenarios, an exact optimiser captures **+30% more preference-weighted value than a sort-by-date baseline at the same travel budget** — and often the *same* value for far fewer kilometres.

The optimiser is **exact** and **pure Python** (zero dependencies — the engine and eval import nothing outside the standard library), and it's **verified against a brute-force oracle** on random instances. The numbers below are produced by `eval/run_eval.py`, not asserted.

---

## Results

35 synthetic events · 5 scenarios · value = sum of your preference weights · travel = round-trip haversine km. Each rung adds one capability.

| scenario | sort-by-date | **optimal** | lift ↑ | optimal travel km |
|---|--:|--:|--:|--:|
| Florida reggae summer | 10 | **18** | **+80%** | 7,117 |
| Sampler (mixed) | 7 | **11** | **+57%** | 2,201 |
| West coast run | 9 | **10** | **+11%** | 1,828 |
| Red Rocks weekend | 5 | **5** | +0% | 44 |
| Northeast sprint | 8 | **8** | +0% | 895 |

**Across the 5 scenarios the exact optimiser captures +30% more value than sort-by-date at the same budget.**

The full ablation (`by-date → by-prize → distance-aware → optimal`, with travel km and value-per-1000km for each) is in [`eval/results.md`](eval/results.md).

### How to read this

- **The greedy baselines aren't dumb — they're locally reasonable and globally wrong.** *Sort-by-date* fills the calendar front-to-back and runs out of budget before your best later shows. *Prize-greedy* grabs your favourites first but ignores geography, so it spends the budget zig-zagging the country. *Distance-aware* greedy stays cheap but skips high-value shows that need a longer hop. Each optimises one thing; the trip needs all of them traded off at once.
- **Same value, fewer kilometres.** In *Florida reggae summer*, prize-greedy and the optimiser both reach value 18 — but the optimiser does it in **7,117 km vs 11,337 km**. Capturing the same value for 37% less travel is the kind of win a sort can't find.
- **Honest about the no-ops.** In *Red Rocks weekend* and *Northeast sprint* the optimiser ties the baseline (**+0%**): when the window is short and the budget loose, greedy already finds the optimum. A method that "always wins" on every scenario would be a sign the scenarios were cherry-picked.

---

## How it works

Because every event has a **fixed date**, the visit order is forced by the calendar. That collapses the usual travelling-salesman *ordering* problem into a **selection** problem: a resource-constrained longest path on a date-ordered DAG.

- **Nodes** = the in-window events in date order; **edges** `i → j` exist only when `j` is later and the hop is travel-feasible (you can cover the distance in the days between them). Because edges only go forward in time, there are **no subtours to eliminate**.
- Each node carries a **prize** (your preference weight); each edge and home-leg carries **kilometres**.
- We want the max-prize `home → events → home` path whose total kilometres fit the **budget** (and an optional event cap).

`plan_optimal` solves this **exactly** with **Pareto label-setting** (dynamic programming with dominance pruning): at each event it keeps only the partial itineraries that aren't beaten on both resources *and* value. No ILP solver, no external service. `tests/test_optimizer.py` proves it matches a brute-force oracle on 40 random instances.

| file | role |
|---|---|
| `src/gigtrip/model.py` | `Event`, `Constraints`, `Itinerary`, preference `prize()` |
| `src/gigtrip/distance.py` | haversine great-circle km |
| `src/gigtrip/optimizer.py` | greedy baselines + the exact Pareto optimiser + brute-force oracle |
| `src/gigtrip/data.py` | synthetic corpus loader + optional live Bandsintown feed |
| `eval/run_eval.py` | the ablation that produces the table above |
| `app/gigtrip_live.py` | the Streamlit UI, wired to the engine |

---

## Quickstart

```bash
# engine + eval + tests need NOTHING but Python (standard library only)
python eval/run_eval.py                  # reproduce the results table
python -m pytest -q                      # 54 tests incl. brute-force equivalence

# the interactive app
pip install -r requirements.txt          # streamlit + pandas + plotly + requests
streamlit run app/gigtrip_live.py
```

Live shows come from Bandsintown when `BANDSINTOWN_APP_ID` is set; otherwise the app runs on the bundled synthetic corpus — the reproducible default.

---

## Honest scope

- **Travel cost is straight-line haversine km, not road/airfare routing.** It is monotonic in real travel cost, which is what the *selection* needs; swapping in a routing/airfare API turns the kilometre budget into a dollar budget without touching the optimiser.
- **The corpus is synthetic and deterministic** (`data/events.json`) so the eval reproduces for anyone; the live Bandsintown feed is an optional front door, not the measured surface.
- **Preference value is a user-supplied weight per artist/team**, not a learned model — the point is the *optimisation*, not the scoring.
- The model assumes you attend each chosen event on its date and travel point-to-point between consecutive ones; it doesn't model lodging, multi-leg flights, or per-event ticket cost (all natural extensions on top of the same path formulation).

MIT-licensed.

---

## Context

Part of [**axiom-orion**](https://github.com/axiom-orion) — small, eval-driven engineering pieces that each turn one hand-waved claim into a reproducible number. The "constraint-optimisation, not a sort" framing and the brute-force-verified exact solver shown here are the same discipline the [**Vorion**](https://github.com/vorionsys) governed-AI platform (`@vorionsys/*`) applies to autonomous agents: measure the lift, prove the method, scope it honestly. Built by [Ryan Cason](https://github.com/vorionsys).
