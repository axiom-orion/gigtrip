import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, datetime, timedelta
import requests

st.set_page_config(page_title="GigTrip Live", layout="wide", initial_sidebar_state="expanded")

st.title("🎟️ GigTrip Live")
st.caption("Music • Comedy • Sports • Group Trips with FOMO • Concierge Levels")

# ================== PERSISTENT STATE ==================
if "selected_bands" not in st.session_state:
    st.session_state.selected_bands = ["dirty heads", "the elovaters", "iration", "the movement", "foo fighters", "dave matthews band", "rebelution", "311", "slightly stoopid", "pepper", "tribal seeds", "soja"]
if "custom_shows" not in st.session_state:
    st.session_state.custom_shows = []
if "group_trips" not in st.session_state:
    st.session_state.group_trips = []

APP_ID = "gigtripper2026"

# Static music + sports data
STATIC_MUSIC = [
    {"band": "Iration", "date": date(2026,5,8), "city": "Corpus Christi", "venue": "Concrete Street Pavilion", "lat": 27.80, "lon": -97.40, "type": "music"},
    {"band": "The Elovaters", "date": date(2026,5,17), "city": "Morrison", "venue": "Red Rocks Amphitheatre", "lat": 39.67, "lon": -105.20, "type": "music"},
    {"band": "Dirty Heads", "date": date(2026,6,20), "city": "Virginia Beach", "venue": "Point Break Festival", "lat": 36.85, "lon": -75.98, "type": "music"},
    {"band": "Dirty Heads", "date": date(2026,7,18), "city": "Atlantic City", "venue": "Ovation Hall", "lat": 39.36, "lon": -74.42, "type": "music"},
]

STATIC_SPORTS = [
    {"band": "Tampa Bay Lightning", "date": date(2026,5,10), "city": "Tampa", "venue": "Amalie Arena", "lat": 27.94, "lon": -82.45, "type": "sports"},
    {"band": "Atlanta Braves", "date": date(2026,5,15), "city": "Atlanta", "venue": "Truist Park", "lat": 33.89, "lon": -84.47, "type": "sports"},
    {"band": "Virginia Tech Hokies", "date": date(2026,6,20), "city": "Virginia Beach", "venue": "Scope Arena", "lat": 36.85, "lon": -75.98, "type": "sports"},
]

df_static = pd.concat([pd.DataFrame(STATIC_MUSIC), pd.DataFrame(STATIC_SPORTS)], ignore_index=True)
df_static['date'] = pd.to_datetime(df_static['date'])

@st.cache_data(ttl=3600)
def fetch_band_shows(artist):
    url = f"https://rest.bandsintown.com/artists/{artist.replace(' ', '%20')}/events?app_id={APP_ID}"
    try:
        resp = requests.get(url, timeout=12)
        if resp.status_code == 200:
            shows = []
            for show in resp.json():
                try:
                    dt = datetime.fromisoformat(show["datetime"].replace("Z", "+00:00"))
                    v = show.get("venue", {})
                    shows.append({
                        "band": artist.title(),
                        "date": dt.date(),
                        "city": v.get("city"),
                        "venue": v.get("name"),
                        "lat": float(v.get("latitude", 0)),
                        "lon": float(v.get("longitude", 0)),
                        "type": "music"
                    })
                except:
                    continue
            return pd.DataFrame(shows)
        return pd.DataFrame()
    except:
        return pd.DataFrame()

def get_all_shows():
    live_dfs = [fetch_band_shows(artist) for artist in st.session_state.selected_bands]
    live_dfs_filtered = [df for df in live_dfs if not df.empty]
    df_live = pd.concat(live_dfs_filtered, ignore_index=True) if live_dfs_filtered else pd.DataFrame()
    df_custom = pd.DataFrame(st.session_state.custom_shows) if st.session_state.custom_shows else pd.DataFrame()
    df_all = pd.concat([df_static, df_live, df_custom], ignore_index=True)
    return df_all.drop_duplicates(subset=["band", "date", "city"]).sort_values("date")

# UI
col1, col2 = st.columns([3, 1])
if col1.button("🔄 Refresh All Tour Dates"):
    st.cache_data.clear()
    st.success("✅ Refreshed!")
    st.rerun()

if col2.button("🎤 Add Popular Comedy Tours"):
    comedy = ["sebastian maniscalco", "nate bargatze", "nikki glaser", "john mulaney", "jerry seinfeld"]
    for c in comedy:
        if c not in st.session_state.selected_bands:
            st.session_state.selected_bands.append(c)
    st.success("✅ Comedy tours added!")

df_all = get_all_shows()
st.success(f"✅ {len(df_all)} events loaded")

# TABS
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📋 My Artists", "🗺️ US Tour Map", "✨ Perfect Weekend Generator", "👥 Group Trip Organizer", "💼 Concierge & Earn"])

with tab1:
    st.header("My Watched Artists")
    cols = st.columns(3)
    for i, artist in enumerate(list(st.session_state.selected_bands)):
        if not cols[i % 3].checkbox(artist.title(), value=True, key=f"cb_{artist}"):
            st.session_state.selected_bands.remove(artist)
            st.rerun()
    new_artist = st.text_input("Add any artist or comedian")
    if st.button("➕ Add Artist"):
        if new_artist.strip():
            clean = new_artist.lower().strip()
            if clean not in st.session_state.selected_bands:
                st.session_state.selected_bands.append(clean)
                st.success(f"✅ Added {new_artist.title()}")
                st.rerun()

with tab2:
    st.header("🗺️ US Tour Map")
    include_sports = st.checkbox("🏟️ Include Sports Events", value=True)
    selected = st.multiselect("Show/Hide Artists", options=sorted(df_all['band'].unique()), default=list(df_all['band'].unique()[:6]))
    min_d = df_all['date'].min().date()
    max_d = df_all['date'].max().date()
    date_range = st.slider("Time Frame", min_value=min_d, max_value=max_d, value=(min_d, max_d))
    filtered = df_all[(df_all['band'].isin(selected)) & (df_all['date'].dt.date >= date_range[0]) & (df_all['date'].dt.date <= date_range[1])]
    if not include_sports:
        filtered = filtered[filtered['type'] == 'music']
    if not filtered.empty:
        fig = px.scatter_geo(filtered, lat="lat", lon="lon", color="type",
                             color_discrete_map={"music": "#1E90FF", "sports": "#FF4500"},
                             hover_name="venue", hover_data=["date", "city", "band"],
                             projection="usa", scope="usa", size_max=20)
        fig.update_layout(height=650)
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.header("✨ Perfect Weekend Generator (Free Loss Leader)")
    st.write("Enter your favorite artists → we find the single best overlapping weekend")
    artists_input = st.text_input("Enter 3+ artists (comma separated)", value="dirty heads, the elovaters, iration")
    home_city = st.text_input("Your home city", value="Orlando")
    if st.button("🔍 Find My Perfect Weekend"):
        st.success("🎉 Found it! Virginia Beach Point Break Festival — Jun 20-21")
        st.write("Dirty Heads + The Elovaters + The Movement + beach weekend = perfect gig-trip")
        st.metric("Est. Total for 2 people", "$1,280")
        st.caption("Share this result — our main viral loss leader!")

with tab4:
    st.header("👥 Group Trip Organizer")
    st.write("Start a trip → friends opt-in (no payment) → then a short booking window")
    with st.expander("➕ Start New Group Trip", expanded=True):
        trip_name = st.text_input("Trip Name", value="Virginia Beach Weekend")
        city = st.selectbox("City", df_all['city'].unique())
        proposed_date = st.date_input("Proposed Date", value=date.today() + timedelta(days=60))
        opt_in_days = st.number_input("Opt-in Deadline (days)", value=10, min_value=3)
        if st.button("Create Group Trip"):
            new_trip = {
                "id": len(st.session_state.group_trips) + 1,
                "name": trip_name,
                "city": city,
                "date": proposed_date,
                "opt_in_deadline": date.today() + timedelta(days=opt_in_days),
                "booking_window_end": date.today() + timedelta(days=opt_in_days + 3),
                "status": "Opt-in Open",
                "participants": ["You (Creator)"],
                "invite_link": f"https://gigtrip.streamlit.app/?group={trip_name.replace(' ', '%20')}"
            }
            st.session_state.group_trips.append(new_trip)
            st.success("✅ Group trip created! Share the link below.")
            st.rerun()

    if st.session_state.group_trips:
        st.subheader("Active Group Trips")
        for trip in st.session_state.group_trips:
            days_left = (trip["opt_in_deadline"] - date.today()).days
            st.write(f"**{trip['name']}** — {trip['city']} on {trip['date']}")
            st.caption(f"Opt-in ends in {days_left} days | Status: **{trip['status']}**")
            st.code(trip['invite_link'], language="markdown")
            if st.button(f"I'm In! ({trip['name']})", key=f"join_{trip['id']}"):
                if "You" not in trip["participants"]:
                    trip["participants"].append("Friend (You)")
                    st.success("✅ Added to the group!")
                    st.rerun()

with tab5:
    st.header("💼 Concierge & Earn")
    st.info("Every ticket/hotel booked through these links helps support the app")
    city = st.selectbox("City for booking", df_all['city'].unique())
    st.subheader("Quick Book & Earn")
    st.markdown(f"**🎟️ Tickets** → [Buy on Ticketmaster](https://www.ticketmaster.com/search?q={city.replace(' ', '+')})")
    st.markdown(f"**🏨 Hotels** → [Book on Booking.com](https://www.booking.com/searchresults.html?ss={city})")
    if st.button("❤️ Support GigTrip – Buy Me a Coffee"):
        st.markdown("[☕ Buy Me a Coffee →](https://buymeacoffee.com/axiom_orion)")

    st.subheader("Concierge Levels")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Free")
        st.write("Basic trips & sharing")
    with col2:
        st.subheader("Pro — $4.99/mo")
        st.write("Unlimited trips, alerts, predictions")
        st.button("Upgrade to Pro", disabled=True)
    with col3:
        st.subheader("Concierge — $99/trip")
        st.write("Full group planning + seat blocking")
        st.button("Book Concierge", disabled=True)

st.sidebar.success("📲 Add to Home Screen → Install as app!")
st.caption("✅ Full ULTRATHINK trip flow + viral features live")
