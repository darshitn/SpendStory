"""Smoke tests for the Streamlit UI using AppTest."""

from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest
from src.storage import Database

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
        if section == "Model Evaluation":
            results = next(item.value for item in at.html if 'class="evaluation-results"' in item.value)
            assert "<strong>5</strong>Correctly categorized" in results
            assert "<strong>13</strong>Asked for human review" in results
            assert "<strong>0</strong>Wrong category" in results

    at.selectbox(key="selected_month").select("2026-11").run()
    assert not at.exception
    assert at.query_params["month"] == "2026-11"
    assert any("November 2026" in item.value for item in at.html)

    at.text_input(key="search_query").set_value("canteen").run()
    assert not at.exception
    assert at.sidebar.radio(key="active_nav").value == "Transactions"
    assert at.query_params["nav"] == "Transactions"


def test_drilldown_and_filtering():
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.query_params.update(nav="Transactions", month="2026-10")
    at.session_state["tx_cat_filter"] = "Food"
    at.session_state["tx_type_filter"] = "expense"
    at.run()
    assert not at.exception
    assert at.sidebar.radio(key="active_nav").value == "Transactions"


def test_overview_budget_shortcut_and_slider_save(monkeypatch, tmp_path):
    ledger_path = str(tmp_path / "budgets.db")
    monkeypatch.setenv("FINANCE_DB_PATH", ledger_path)
    ledger = Database(ledger_path)
    ledger.set_budget("2026-10", "Food", 123456)
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.query_params.update(nav="Overview", month="2026-10")
    at.run()
    at.button(key="btn_goto_budgets").click().run()
    assert not at.exception
    assert at.query_params["nav"] == "Budgets"
    assert at.query_params["month"] == "2026-10"

    at.button(key="configure_budgets").click().run()
    assert at.select_slider(key="budget_slider_2026-10_Food").value == 123456
    at.toggle(key="budget_track_2026-10_Transport").set_value(True).run()
    at.select_slider(key="budget_slider_2026-10_Transport").set_value(50000).run()
    at.button(key="cancel_budget_targets").click().run()
    assert ledger.get_budgets("2026-10") == {"Food": 123456}

    at.button(key="configure_budgets").click().run()
    at.toggle(key="budget_track_2026-10_Food").set_value(False).run()
    at.toggle(key="budget_track_2026-10_Transport").set_value(True).run()
    at.button(key="save_budget_targets").click().run()
    assert not at.exception
    assert ledger.get_budgets("2026-10") == {"Transport": 0}


def test_hosted_demo_seeds_and_isolates_each_session(monkeypatch, tmp_path):
    monkeypatch.setenv("SPENDSTORY_DEMO", "1")
    local_path = tmp_path / "local.db"
    monkeypatch.setenv("FINANCE_DB_PATH", str(local_path))
    first = AppTest.from_file(APP_PATH, default_timeout=30).run()
    assert not first.exception
    assert first.query_params["month"] == "2026-11"
    first_db = first.session_state["demo_db"]
    assert len(first_db.get_transactions()) == 218
    first_db.set_budget("2026-10", "Food", 123456)
    first.run()
    assert first.session_state["demo_db"].get_budgets("2026-10")["Food"] == 123456

    second = AppTest.from_file(APP_PATH, default_timeout=30).run()
    assert not second.exception
    assert second.session_state["demo_db"].get_budgets("2026-10")["Food"] == 200000
    assert not local_path.exists()
