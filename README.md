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
