"""Smoke tests for the Streamlit UI using AppTest."""

from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")


def test_app_startup_and_render():
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    assert not at.exception
    assert any("SpendStory" in str(h.value) for h in at.html)


def test_app_navigation_and_views():
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.query_params.update(nav="Overview", month="2026-10")
    at.run()
    assert not at.exception

    for section in ("Transactions", "Budgets", "Category Review", "Model Evaluation", "Overview"):
        at.sidebar.radio(key="active_nav").set_value(section).run()
        assert not at.exception
        assert any(f'>{section}</h1>' in item.value for item in at.html)
        assert at.query_params["nav"] == section

    at.selectbox(key="selected_month").select("2026-11").run()
    assert not at.exception
    assert at.query_params["month"] == "2026-11"
    assert any("November 2026" in item.value for item in at.html)

    at.text_input(key="search_query").set_value("canteen").run()
    assert not at.exception
    assert at.sidebar.radio(key="active_nav").value == "Transactions"
    assert at.query_params["nav"] == "Transactions"
