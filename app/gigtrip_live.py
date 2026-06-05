"""GigTrip — plan the *optimal* live-event road trip (Streamlit UI over the gigtrip engine).

The hero is the Trip Optimizer: it runs the exact itinerary optimiser from `gigtrip` and
shows how much more preference-weighted value it captures than the naive sort-by-date plan.
Live shows come from Bandsintown when BANDSINTOWN_APP_ID is set; otherwise it runs on the
bundled synthetic corpus (the reproducible default).
"""
from __future__ import annotations

import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd  # noqa: E402
import plotly.express as px  # noqa: E402
import streamlit as st  # noqa: E402

from gigtrip import (  # noqa: E402
    Constraints,
    fetch_bandsintown,
    load_corpus,
    plan_by_date,
    plan_optimal,
)

st.set_page_config(page_title="GigTrip", layout="wide", initial_sidebar_state="expanded")

HOMES = {
    "Orlando, FL": (28.54, -81.38), "Tampa, FL": (27.95, -82.46),
    "Atlanta, GA": (33.75, -84.39), "Nashville, TN": (36.16, -86.78),
    "Denver, CO": (39.74, -104.99), "Austin, TX": (30.27, -97.74),
    "San Diego, CA": (32.72, -117.16), "Los Angeles, CA": (34.05, -118.24),
    "Chicago, IL": (41.88, -87.63), "Boston, MA": (42.36, -71.06),
    "Brooklyn, NY": (40.68, -73.94),
}
WATCHLIST = ["Dirty Heads", "Iration", "Slightly Stoopid", "Rebelution", "The Movement", "SOJA"]


@st.cache_data
def corpus():
    return load_corpus()


def events_df(evs):
    return pd.DataFrame([{"id": e.id, "event": e.title, "kind": e.kind, "date": e.day,
                          "city": e.city, "venue": e.venue, "lat": e.lat, "lon": e.lon}
                         for e in evs])


st.title("🎟️ GigTrip")
st.caption("Plan the **optimal** live-event road trip — not just the soonest shows. "
           "Music • Sports • Comedy • Group Trips")

events = list(corpus())
titles = sorted({e.title for e in events})

# --- sidebar: the trip request ------------------------------------------------ #
st.sidebar.header("Your trip")
home_name = st.sidebar.selectbox("Home base", list(HOMES))
hlat, hlon = HOMES[home_name]
dmin = min(e.day for e in events)
dmax = max(e.day for e in events)
window = st.sidebar.slider("Date window", min_value=dmin, max_value=dmax, value=(dmin, dmax))
budget = st.sidebar.slider("Travel budget (round-trip km)", 500, 20000, 8000, 500)
max_events = st.sidebar.slider("Max events", 1, 10, 6)

live_artist = st.sidebar.text_input("Pull live shows for (Bandsintown, optional)")
if live_artist.strip():
    live = fetch_bandsintown(live_artist.strip())
    if live:
        events += live
        titles = sorted({e.title for e in events})
        st.sidebar.success(f"+{len(live)} live shows for {live_artist.title()}")
    else:
        st.sidebar.info("No live data (set BANDSINTOWN_APP_ID) — using the synthetic corpus.")

tab_opt, tab_map, tab_group, tab_concierge = st.tabs(
    ["🧠 Trip Optimizer", "🗺️ All Events", "👥 Group Trip", "💼 Concierge"])

# ============================ TRIP OPTIMIZER ================================= #
with tab_opt:
    st.subheader("Weight your line-up, then optimize")
    c1, c2 = st.columns(2)
    must = c1.multiselect("Must-see (weight 3)", titles,
                          default=[t for t in titles if t in WATCHLIST])
    like = c2.multiselect("Interested (weight 1)", [t for t in titles if t not in must])
    prefs = {t.lower(): 3.0 for t in must} | {t.lower(): 1.0 for t in like}

    if st.button("🧠 Optimize my trip", type="primary"):
        if not prefs:
            st.warning("Pick at least one artist or team to weight.")
        else:
            c = Constraints(home_name, hlat, hlon, window[0], window[1],
                            max_travel_km=float(budget), max_events=int(max_events))
            opt = plan_optimal(events, prefs, c)
            base = plan_by_date(events, prefs, c)
            m1, m2, m3 = st.columns(3)
            m1.metric("Value captured", f"{opt.value:.0f}",
                      delta=f"{opt.value - base.value:+.0f} vs sort-by-date")
            m2.metric("Events", opt.count)
            m3.metric("Travel", f"{opt.travel_km:,.0f} km",
                      delta=f"{opt.travel_km - base.travel_km:+,.0f} vs baseline",
                      delta_color="inverse")
            if base.value > 0:
                lift = 100 * (opt.value - base.value) / base.value
                st.success(f"The optimizer captures **{lift:+.0f}%** more preference-weighted "
                           f"value than taking the soonest shows — at the same budget.")
            if opt.count == 0:
                st.info("No feasible trip in this window/budget. Loosen the budget or window.")
            else:
                df = events_df(opt.events)
                df["leg #"] = range(1, len(df) + 1)
                st.dataframe(df[["leg #", "date", "event", "kind", "city", "venue"]],
                             hide_index=True, use_container_width=True)
                route = pd.concat([
                    pd.DataFrame([{"event": f"🏠 {home_name}", "lat": hlat, "lon": hlon}]),
                    df[["event", "lat", "lon"]],
                    pd.DataFrame([{"event": f"🏠 {home_name}", "lat": hlat, "lon": hlon}]),
                ], ignore_index=True)
                fig = px.line_geo(route, lat="lat", lon="lon", text="event",
                                  scope="usa", markers=True)
                fig.update_traces(line_color="#1E90FF", textposition="top center")
                fig.update_layout(height=560, margin=dict(l=0, r=0, t=10, b=0))
                st.plotly_chart(fig, use_container_width=True)
                st.session_state["last_trip"] = {"home": home_name, "events": list(opt.ids())}

    with st.expander("Why not just sort by date? (the point this app makes)"):
        st.markdown(
            "Sort-by-date fills the calendar front-to-back and runs out of budget before your "
            "best later shows; prize-greedy grabs favourites but zig-zags the country. The trip "
            "needs preference, geography, and the calendar traded off **at once** — a constrained "
            "optimisation, solved exactly. See the eval in the repo README.")

# ============================ ALL EVENTS MAP ================================= #
with tab_map:
    st.subheader("🗺️ Every event in the window")
    df = events_df([e for e in events if window[0] <= e.day <= window[1]])
    df = df[(df["lat"] != 0) & (df["lon"] != 0)]
    if df.empty:
        st.info("No events in this window.")
    else:
        fig = px.scatter_geo(df, lat="lat", lon="lon", color="kind", hover_name="venue",
                             hover_data=["event", "date", "city"], scope="usa",
                             color_discrete_map={"music": "#1E90FF", "sports": "#FF4500",
                                                 "comedy": "#2ca02c"})
        fig.update_layout(height=620, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

# ============================ GROUP TRIP ===================================== #
with tab_group:
    st.subheader("👥 Group Trip Organizer")
    seed = st.session_state.get("last_trip")
    if seed:
        st.caption(f"Seeded from your optimized trip out of {seed['home']} "
                   f"({len(seed['events'])} events).")
    name = st.text_input("Trip name", value="Reggae Road Trip 2026")
    proposed = st.date_input("Proposed start", value=date.today() + timedelta(days=45))
    if st.button("Create group trip"):
        st.session_state.setdefault("trips", []).append({"name": name, "date": proposed})
        st.success("✅ Group trip created — share the link with friends to opt in.")
    for t in st.session_state.get("trips", []):
        st.write(f"**{t['name']}** — proposed {t['date']}")

# ============================ CONCIERGE ====================================== #
with tab_concierge:
    st.subheader("💼 Concierge & Booking")
    st.info("Tickets/hotels booked through these links support the app.")
    city = st.selectbox("City", sorted({e.city for e in events}))
    st.markdown(f"🎟️ [Tickets on Ticketmaster](https://www.ticketmaster.com/search?q={city})  ·  "
                f"🏨 [Hotels on Booking.com](https://www.booking.com/searchresults.html?ss={city})")
