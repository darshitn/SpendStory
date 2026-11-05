"""Interactive dashboard charts backed by the app's existing analytics."""

from collections.abc import Sequence
from pathlib import Path

import streamlit as st


_ASSETS = Path(__file__).parent
_CHART = st.components.v2.component(
    "nexora_dashboard_chart",
    html='<div class="finance-chart"></div>',
    js=(_ASSETS / "dashboard_charts.js").read_text(encoding="utf-8"),
    css=(_ASSETS / "dashboard_charts.css").read_text(encoding="utf-8"),
)


def render_trend(rows: Sequence[dict], *, key: str = "dashboard_trend") -> None:
    """Render dated cumulative income and expense records in rupees."""
    _CHART(key=key, data={"kind": "trend", "rows": list(rows)})


def render_donut(rows: Sequence[dict], *, key: str = "dashboard_donut") -> None:
    """Render expense records with Category and Amount fields."""
    _CHART(key=key, data={"kind": "donut", "rows": list(rows)})


def render_monthly(rows: Sequence[dict], *, selected_month: str, key: str) -> None:
    """Render monthly totals and apply month selections before widgets rerender."""
    months = {row["year_month"] for row in rows}

    def select_month() -> None:
        month = st.session_state[key].month_selected
        if isinstance(month, str) and month in months:
            st.session_state.selected_month = month

    _CHART(
        key=key,
        data={"kind": "monthly", "rows": list(rows), "selectedMonth": selected_month},
        on_month_selected_change=select_month,
    )
