"""Loading events: the bundled **synthetic corpus** (the reproducible default that the eval
and tests run on) and an optional **live Bandsintown feed** (env-keyed, best-effort).
"""
from __future__ import annotations

import json
import os
from datetime import date, datetime
from pathlib import Path

from .model import Event

ROOT = Path(__file__).resolve().parents[2]
CORPUS_PATH = ROOT / "data" / "events.json"


def _to_event(row: dict) -> Event:
    return Event(
        id=row["id"], title=row["title"], kind=row["kind"],
        day=date.fromisoformat(row["day"]), city=row["city"], venue=row["venue"],
        lat=float(row["lat"]), lon=float(row["lon"]))


def load_corpus(path: str | Path | None = None) -> list[Event]:
    """The fixed synthetic event corpus — deterministic, no network, the eval/test default."""
    p = Path(path) if path else CORPUS_PATH
    return [_to_event(r) for r in json.loads(p.read_text(encoding="utf-8"))]


def fetch_bandsintown(artist: str, app_id: str | None = None) -> list[Event]:
    """Optional live feed. Returns [] on any error or missing key, so the synthetic corpus
    stays the reproducible default and the UI never hard-fails on the network."""
    app_id = app_id or os.environ.get("BANDSINTOWN_APP_ID")
    if not app_id:
        return []
    try:
        import requests
        slug = artist.replace(" ", "%20")
        url = f"https://rest.bandsintown.com/artists/{slug}/events?app_id={app_id}"
        resp = requests.get(url, timeout=12)
        if resp.status_code != 200:
            return []
        out: list[Event] = []
        for show in resp.json():
            try:
                dt = datetime.fromisoformat(show["datetime"].replace("Z", "+00:00"))
                v = show.get("venue", {})
                lat, lon = float(v.get("latitude", 0) or 0), float(v.get("longitude", 0) or 0)
                if lat == 0 and lon == 0:
                    continue
                out.append(Event(
                    id=f"live-{artist}-{dt.date().isoformat()}".replace(" ", "_").lower(),
                    title=artist.title(), kind="music", day=dt.date(),
                    city=v.get("city", "?"), venue=v.get("name", "?"), lat=lat, lon=lon))
            except (KeyError, ValueError, TypeError):
                continue
        return out
    except Exception:
        return []
