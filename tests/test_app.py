"""Smoke test for the Streamlit UI via Streamlit's AppTest harness.

Skipped automatically where streamlit isn't installed (e.g. CI runs only the pure-Python
engine + eval), so it never forces the UI stack into the engine's dependency set.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

APP = str(Path(__file__).resolve().parents[1] / "app" / "gigtrip_live.py")


def test_app_loads_without_exception():
    at = AppTest.from_file(APP).run(timeout=60)
    assert not at.exception, at.exception


def test_optimize_button_runs():
    at = AppTest.from_file(APP).run(timeout=60)
    assert not at.exception
    optimize = [b for b in at.button if "Optimize" in (b.label or "")]
    assert optimize, "optimize button not found"
    optimize[0].click().run(timeout=60)
    assert not at.exception, at.exception
    # the default watchlist is feasible -> the optimizer renders a result
    assert at.dataframe or any("value" in (m.label or "").lower() for m in at.metric)
