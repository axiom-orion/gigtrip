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
# GigTrip Live

A single-file **Streamlit app for planning trips around live events** — music, comedy, and sports. It tracks the tour dates of artists and teams you follow (live from the Bandsintown API), plots upcoming events on a US map, lets you spin up a no-payment "opt-in" group trip with a shareable invite link, and surfaces ticket/hotel booking links plus tiered concierge offers. The whole app is one script — `gigtrip-live.py` — and runs locally with four dependencies.

This README describes what the code in this repo actually does today. Where a feature is a demo placeholder or a roadmap item, it says so.

---

## Features

The app opens with a global artist/team watchlist and five tabs:

- **📋 My Artists** — manage your watchlist. Add any artist or comedian by name, toggle the ones you follow on/off, and one-click add a seed list of popular comedy tours. Each followed name is queried against Bandsintown.
- **🗺️ US Tour Map** — a Plotly `scatter_geo` (Albers-USA projection) of upcoming events. Filter by artist, by date range (slider), and toggle sports on/off. Events with no usable coordinates are dropped so the map doesn't break.
- **✨ Perfect Weekend Generator** — enter a few artists and a home city to "find the single best overlapping weekend." **This tab currently returns a hardcoded demo result** (see *Status* below); the inputs are collected but not yet used to compute anything.
- **👥 Group Trip Organizer** — start a group trip (name, city, proposed date, opt-in deadline). It generates a shareable invite link and tracks an opt-in → booking-window status. Friends opt in with no payment up front. **State lives in `st.session_state` and is lost on reload** — there is no backend or persistence yet.
- **💼 Concierge & Earn** — booking links for the selected city (Ticketmaster, Booking.com), a Buy-Me-a-Coffee support link, and three concierge tiers: Free, Pro ($4.99/mo), and Concierge ($99/trip). The Pro/Concierge upgrade buttons are present but **disabled** — there is no payment flow.

The data shown is the union of three sources, de-duplicated on `(band, date, city)` and sorted by date: a small static seed list, live Bandsintown results for everyone on your watchlist, and any custom events held in session state.

---

## Quickstart

```bash
pip install -r requirements.txt
streamlit run gigtrip-live.py
```

Then open the URL Streamlit prints (default `http://localhost:8501`). No API key or `.env` is required — the Bandsintown `app_id` is hardcoded in the script.

Dependencies (`requirements.txt`): `streamlit`, `pandas`, `requests`, `plotly`.

---

## Data sources

- **Bandsintown API** — live tour dates per watched artist/team, fetched from `https://rest.bandsintown.com/artists/{artist}/events` using the public `app_id` `gigtripper2026` (defined as `APP_ID` in the script). Responses are cached for one hour (`@st.cache_data(ttl=3600)`); the **🔄 Refresh All Tour Dates** button clears the cache. Network/parse errors fall back to an empty result so the app keeps running.
- **Static seed data** — a few hand-entered music and sports events (`STATIC_MUSIC`, `STATIC_SPORTS`) with fixed lat/lon, so the map and tabs have content even before any live results return. These are illustrative sample rows, not a maintained dataset.
- **Custom events** — events added at runtime, held in `st.session_state.custom_shows` (in-memory only).

---

## Status / not yet built

This is an early, single-file prototype. Honest about what is and isn't real:

- **The Perfect Weekend Generator is a demo.** The button currently prints a fixed, hardcoded result (a Virginia Beach festival weekend and an illustrative `$1,280` estimate). It does **not** read the artist/city inputs, query overlapping dates, or compute a cost. A real weekend-finder — match overlapping tour dates near a home city, rank candidates, and estimate cost — is roadmap, and any "best weekend" or value claim should be backed by a measurable evaluation before it appears here. There is no optimizer and no eval in this repo today.
- **No persistence / no backend.** Watchlist, custom events, and group trips live in Streamlit session state and reset on reload. Invite links point at a Streamlit-hosted URL but there is no server to resolve them, so opt-ins are local to one session.
- **Monetization is stubbed.** The Pro and Concierge upgrade buttons are disabled; there is no payments integration. The Ticketmaster/Booking.com links are plain search URLs, not tracked affiliate links yet.
- **Static data is illustrative**, not a curated or refreshed source.

Roadmap, roughly in order: a real overlapping-weekend finder plus an evaluation to justify any quality/value claim; durable storage for watchlists and group trips; working invite-link resolution and opt-in tracking; and real affiliate/payment wiring behind the concierge tiers.

---

## License

MIT — © Ryan Cason.
