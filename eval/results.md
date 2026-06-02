# gigtrip — itinerary optimisation eval

35 synthetic events · 5 scenarios · value = sum of preference weights · travel = round-trip haversine km.


**Headline:** across 5 scenarios the exact optimiser captures **+30%** more preference-weighted value than the sort-by-date baseline at the same travel budget.


## Florida reggae summer
home **Orlando** · 2026-05-01→2026-08-31 · budget 12000 km · ≤6 events

| planner | events | value ↑ | travel km ↓ | value/1000km ↑ |
|---|--:|--:|--:|--:|
| by-date | 6 | 10 | 7757 | 1.29 |
| by-prize | 6 | 18 | 11337 | 1.59 |
| distance-aware | 6 | 12 | 2645 | 4.54 |
| **optimal** | 6 | 18 | 7117 | 2.53 |

_optimal captures **+80%** value vs. sort-by-date, same budget._

## Red Rocks weekend
home **Denver** · 2026-05-15→2026-05-19 · budget 1500 km · ≤2 events

| planner | events | value ↑ | travel km ↓ | value/1000km ↑ |
|---|--:|--:|--:|--:|
| by-date | 2 | 5 | 44 | 113.89 |
| by-prize | 2 | 5 | 44 | 113.89 |
| distance-aware | 2 | 5 | 44 | 113.89 |
| **optimal** | 2 | 5 | 44 | 113.89 |

_optimal captures **+0%** value vs. sort-by-date, same budget._

## West coast run
home **San Diego** · 2026-05-20→2026-06-10 · budget 6000 km · ≤4 events

| planner | events | value ↑ | travel km ↓ | value/1000km ↑ |
|---|--:|--:|--:|--:|
| by-date | 4 | 9 | 1486 | 6.06 |
| by-prize | 4 | 10 | 1828 | 5.47 |
| distance-aware | 4 | 8 | 970 | 8.25 |
| **optimal** | 4 | 10 | 1828 | 5.47 |

_optimal captures **+11%** value vs. sort-by-date, same budget._

## Northeast sprint
home **Boston** · 2026-07-01→2026-07-31 · budget 2500 km · ≤3 events

| planner | events | value ↑ | travel km ↓ | value/1000km ↑ |
|---|--:|--:|--:|--:|
| by-date | 3 | 8 | 895 | 8.94 |
| by-prize | 3 | 8 | 895 | 8.94 |
| distance-aware | 3 | 8 | 895 | 8.94 |
| **optimal** | 3 | 8 | 895 | 8.94 |

_optimal captures **+0%** value vs. sort-by-date, same budget._

## Sampler (mixed)
home **Atlanta** · 2026-06-01→2026-07-15 · budget 7000 km · ≤5 events

| planner | events | value ↑ | travel km ↓ | value/1000km ↑ |
|---|--:|--:|--:|--:|
| by-date | 5 | 7 | 5357 | 1.31 |
| by-prize | 5 | 11 | 4829 | 2.28 |
| distance-aware | 5 | 10 | 1319 | 7.58 |
| **optimal** | 5 | 11 | 2201 | 5.00 |

_optimal captures **+57%** value vs. sort-by-date, same budget._

---

**Honest scope.** Travel cost is straight-line haversine km, not road/airfare routing (monotonic in real cost, which is what the selection needs). The corpus is synthetic and deterministic; live Bandsintown data is an optional front door. The optimiser is exact (Pareto label-setting), verified against brute force in `tests/`.
