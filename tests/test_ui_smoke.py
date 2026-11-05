"""Smoke tests for the Streamlit UI using AppTest."""

from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")


def test_app_startup_and_render():
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    assert not at.exception
    # Verify Nexora branding is present
    assert any("Nexora" in str(h.value) for h in at.html)


def test_app_navigation_and_views():
    at = AppTest.from_file(APP_PATH, default_timeout=30)
    at.run()
    assert not at.exception

    # Radio options: ["Overview", "Transactions", "Budgets", "Category Review...", "Model Evaluation"]
    radio = at.sidebar.radio[0]
    assert "Overview" in radio.options

    # Switch to Transactions
    radio.set_value("Transactions").run()
    assert not at.exception

    # Switch to Budgets
    radio = at.sidebar.radio[0]
    radio.set_value("Budgets").run()
    assert not at.exception

    # Switch to Model Evaluation
    radio = at.sidebar.radio[0]
    radio.set_value("Model Evaluation").run()
    assert not at.exception
