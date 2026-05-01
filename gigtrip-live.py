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

# ================== UI ==================
col1, col2 = st.columns([3, 1])
if col1.button("🔄 Refresh All Tour Dates"):
    st.cache_data.clear()
    st.success("✅ Refreshed from Bandsintown!")
    st.rerun()

if col2.button("🎤 Add Popular Comedy Tours"):
    comedy = ["sebastian maniscalco", "nate bargatze", "nikki glaser", "john mulaney", "jerry seinfeld"]
    for c in comedy:
        if c not in st.session_state.selected_bands:
            st.session_state.selected_bands.append(c)
    st.success("✅ Comedy tours added!")

df_all = get_all_shows()
st.success(f"✅ {len(df_all)} events loaded (music + sports)")

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

with tab3:  # Loss Leader
    st.header("✨ Perfect Weekend Generator (Free)")
    st.write("Enter your favorite artists → we find the single best overlapping weekend")
    artists_input = st.text_input("Enter 3+ artists (comma separated
