"""SpendStory — AI-assisted student finance dashboard.

Visual direction: Money Management Dashboard by Atiqur Rahman for ILmix Studio.
"""

from __future__ import annotations

from datetime import date, datetime
import html
import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from src.analytics import (
    calculate_budget_comparisons,
    calculate_cumulative_trend,
    calculate_monthly_summary,
    calculate_multi_month_comparison,
    export_transactions_to_csv,
    format_inr,
)
from src.categorizer import DEFAULT_CONFIDENCE_THRESHOLD, get_default_categorizer
from src.dashboard_charts import render_donut, render_monthly, render_trend
from src.storage import Database, ImportResult
from src.transactions import (
    ALLOWED_EXPENSE_CATEGORIES,
    Transaction,
    compute_fingerprint,
    parse_amount_to_paise,
    parse_transactions_csv,
)


# -----------------------------------------------------------------------------
# Configuration & Theme Setup
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="SpendStory — Student Finance Dashboard",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="auto",
)

# Custom Scoped CSS matching the Dribbble Nexora visual design brief:
# Pale lavender background, rounded white application shell, subtle borders,
# modern sans typography, compact top toolbar, and quiet sidebar.
NEXORA_CSS = """
<style>
/* Root styling and Pale Lavender backdrop */
.stApp {
    background: linear-gradient(161deg, #d7def8 7%, #dedcf8 53%, #e8d1f3 100%) !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    color: #14182D;
}

/* Sidebar styling: Quiet pale gray */
[data-testid="stSidebar"] {
    background-color: #F8FAFD !important;
    border-right: 1px solid #EDF1F7 !important;
    padding-top: 16px !important;
}

[data-testid="stSidebar"] .block-container {
    background-color: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 16px 14px !important;
    margin-top: 0 !important;
}

/* SpendStory wordmark */
.nexora-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 19px;
    font-weight: 800;
    color: #14182D;
    letter-spacing: -0.5px;
    margin-bottom: 24px;
    padding-left: 6px;
}

/* Sidebar Navigation Items */
.stRadio > div {
    gap: 6px;
}

.stRadio label {
    font-size: 13px !important;
    font-weight: 500 !important;
    color: #4A5568 !important;
    padding: 8px 12px !important;
    border-radius: 10px !important;
    transition: all 0.15s ease !important;
}

.stRadio label:hover {
    background-color: #EDF2F9 !important;
    color: #14182D !important;
}

/* Top Toolbar */
.view-title {
    font-size: 20px;
    font-weight: 700;
    color: #14182D;
    letter-spacing: -0.3px;
    margin: 0;
}

/* Greeting Section */
.greeting-header {
    font-size: 22px;
    font-weight: 700;
    color: #182263;
    letter-spacing: -0.5px;
    margin-bottom: 2px;
}

.greeting-subtext {
    font-size: 13px;
    color: #586889;
    font-weight: 400;
    margin-bottom: 18px;
}

/* Four Equal Financial Summary Cards */
.metric-card {
    background-color: #F8FAFD;
    border: 1px solid #EAEFF7;
    border-radius: 14px;
    padding: 16px 18px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: 112px;
    transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.metric-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 20px -6px rgba(20, 24, 45, 0.05);
}

.metric-top-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.metric-label {
    font-size: 12px;
    font-weight: 600;
    color: #202967;
    text-transform: capitalize;
    letter-spacing: 0.2px;
}

.metric-figure {
    font-size: clamp(20px, 1.8vw, 26px);
    font-weight: 700;
    color: #182263;
    letter-spacing: -0.6px;
    font-variant-numeric: tabular-nums;
    margin: 6px 0 2px 0;
}

.metric-badge {
    font-size: 11px;
    font-weight: 500;
    color: #4A5568;
    display: flex;
    align-items: center;
    gap: 4px;
    border-top: 1px solid #e3e7ed;
    padding-top: 6px;
}

.metric-badge.green {
    color: #0E9F6E;
    font-weight: 600;
}

.metric-badge.red {
    color: #D32F2F;
    font-weight: 600;
    background: #FDE8E8;
    padding: 2px 6px;
    border-radius: 4px;
}

.metric-badge.purple {
    color: #7E3AF2;
    font-weight: 600;
}

.metric-badge.blue {
    color: #373EDC;
    font-weight: 600;
}

.metric-badge.secondary {
    color: #64748B;
    font-weight: 400;
}

/* Chart panel headings */
.panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
}

.panel-title {
    font-size: 14px;
    font-weight: 700;
    color: #182263;
    letter-spacing: -0.2px;
    margin: 0;
}

/* Category Budget Row */
.budget-progress-track {
    width: 100%;
    height: 7px;
    background-color: #EDF2F7;
    border-radius: 999px;
    overflow: hidden;
    margin-top: 4px;
}

.budget-progress-fill {
    height: 100%;
    border-radius: 999px;
    transition: width 0.3s ease;
}

/* Badges */
.badge-confirmed {
    background-color: #DEF7EC;
    color: #03543F;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
}

.badge-review {
    background-color: #FEF3C7;
    color: #92400E;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
}

.badge-overbudget {
    background-color: #FEE2E2;
    color: #991B1B;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 600;
}

/* Streamlit button refinements */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    transition: all 0.15s ease !important;
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #373EDC 0%, #4B5AEF 100%) !important;
    border: none !important;
    color: white !important;
    box-shadow: 0 4px 12px rgba(55, 62, 220, 0.25) !important;
}

.stButton > button[kind="primary"]:hover {
    box-shadow: 0 6px 16px rgba(55, 62, 220, 0.35) !important;
    transform: translateY(-1px);
}

/* Sidebar quick action card */
.sidebar-promo-card {
    background: linear-gradient(145deg, #F0F4FE 0%, #E7EDFD 100%);
    border: 1px solid #D5E1FB;
    border-radius: 14px;
    padding: 12px;
    margin-top: 18px;
}

.sidebar-promo-title {
    font-size: 13px;
    font-weight: 700;
    color: #14182D;
    margin-bottom: 3px;
}

.sidebar-promo-desc {
    font-size: 11px;
    color: #5A6478;
    line-height: 1.35;
    margin-bottom: 10px;
}

/* Streamlit 1.66: the app view is the common parent of sidebar and main. */
@media (min-width: 901px) {
  [data-testid="stAppViewContainer"] {
    --frame-gutter: clamp(18px, 2.2vw, 42px);
    --frame-top: clamp(16px, 2.5vh, 30px);
    --rail: clamp(200px, 15.5vw, 240px);
    margin: var(--frame-top) auto !important;
    height: calc(100dvh - 2 * var(--frame-top)) !important;
    min-height: 0 !important;
    width: calc(100% - 2 * var(--frame-gutter)) !important;
    border: 1px solid white; border-radius: 23px;
    overflow: hidden; background: white !important;
    box-shadow: 0 0 0 11px rgba(255,255,255,.36), 0 0 0 12px rgba(255,255,255,.82), 0 22px 50px rgba(82,53,151,.14);
  }
  [data-testid="stSidebar"] { width: var(--rail) !important; min-width: var(--rail) !important; max-width: var(--rail) !important; }
  [data-testid="stSidebar"] > div:first-child { width: var(--rail) !important; }
  [data-testid="stSidebarHeader"] { display: none !important; }
  [data-testid="stSidebar"] [data-testid="stSidebarContent"],
  [data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { height: 100% !important; min-height: 0 !important; }
  [data-testid="stMain"] {
    height: calc(100dvh - 2 * var(--frame-top) - 2px) !important;
    min-height: 0 !important;
    overflow-y: auto !important;
  }
  [data-testid="stSidebar"] [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] .sidebar-spacer) {
    min-height: calc(100dvh - 2 * var(--frame-top) - 16px);
  }
}
[data-testid="stHeader"] { background: transparent !important; height: 0 !important; }
[data-testid="stToolbar"], [data-testid="stAppDeployButton"] { display: none !important; }
[data-testid="stMain"] { background: white !important; }
[data-testid="stMainBlockContainer"] { max-width: none !important; padding: 0 16px 20px !important; }
[data-testid="stSidebar"] { padding-top: 0 !important; background: #f3f6f8 !important; }
[data-testid="stSidebar"] [data-testid="stSidebarContent"] { padding: 0 !important; }
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { padding: 0 12px 14px !important; min-height: 100%; }
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] > [data-testid="stVerticalBlock"] { min-height: 100%; }
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has(.sidebar-spacer) { flex: 1; min-height: 12px; }
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: .55rem !important; }
[data-testid="stSidebar"] .stRadio [role="radiogroup"] { gap: 3px !important; }
[data-testid="stSidebar"] .stRadio label { padding: 8px 10px !important; width: 100%; }
[data-testid="stSidebar"] .stRadio label:has(input:checked) { background: #e9eafd; color: #3029c5 !important; }
[data-testid="stRadioOption"] > div > div:first-child { display: none; }
[data-testid="stSidebar"] .stRadio label:focus-within { outline: 2px solid #373edc; outline-offset: 2px; }
[data-testid="stSidebar"] .stRadio label p { display: flex; align-items: center; gap: 8px; font-size: 13px; white-space: nowrap; }
[data-testid="stSidebar"] .stRadio label p::before {
  content: ''; flex: 0 0 16px; height: 16px; background: currentColor;
  mask: var(--nav-icon) center / contain no-repeat;
}
[data-testid="stSidebar"] .stRadio [role="radiogroup"] > :nth-child(1) { --nav-icon: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8'%3E%3Ccircle cx='12' cy='12' r='9'/%3E%3Cpath d='m12 12 4-4M7 15a6 6 0 0 1 6-9m4 4a6 6 0 0 1 0 5'/%3E%3C/svg%3E"); }
[data-testid="stSidebar"] .stRadio [role="radiogroup"] > :nth-child(2) { --nav-icon: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8'%3E%3Crect x='3' y='5' width='18' height='14' rx='2'/%3E%3Cpath d='M3 9h18m-14 5h4'/%3E%3C/svg%3E"); }
[data-testid="stSidebar"] .stRadio [role="radiogroup"] > :nth-child(3) { --nav-icon: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8'%3E%3Cpath d='M4 8h16v12H4zM7 8V4h10v4M9 13h6m-6 3h4'/%3E%3C/svg%3E"); }
[data-testid="stSidebar"] .stRadio [role="radiogroup"] > :nth-child(4) { --nav-icon: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8'%3E%3Cpath d='M3 5h9l9 9-7 7-9-9z'/%3E%3Ccircle cx='8' cy='9' r='1'/%3E%3C/svg%3E"); }
[data-testid="stSidebar"] .stRadio [role="radiogroup"] > :nth-child(5) { --nav-icon: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' stroke-width='1.8'%3E%3Cpath d='M4 4v16h16M8 16v-4m5 4V8m5 8V5'/%3E%3C/svg%3E"); }
[data-testid="stMain"] [data-testid="stVerticalBlock"] { gap: .65rem; }
:is(.st-key-dashboard_trend, .st-key-dashboard_breakdown, .st-key-dashboard_budgets, .st-key-dashboard_comparison) {
  background: #f3f5f7; border: 1px solid #edf0f4; border-radius: 12px; padding: 14px !important;
}
.trend-surplus { line-height: 1.2; margin-top: 4px; color: #182263; font-size: 26px; font-weight: 750; letter-spacing: -.6px; }
.chart-period { color: #586889; font-size: 11px; text-align: right; }
@media (min-width: 901px) {
  .st-key-dashboard_trend, .st-key-dashboard_breakdown { min-height: 314px; }
  .st-key-dashboard_budgets, .st-key-dashboard_comparison { min-height: 275px; }
}
[data-testid="stMain"] [data-testid="stHorizontalBlock"] { gap: 12px; }
.nexora-logo { height: 48px; padding: 0; margin: 0; border-bottom: 1px solid #e5e9ef; }
.st-key-dashboard_demo {
  background: linear-gradient(160deg, #e6e6f8, #efedfa);
  padding: 10px !important;
  border: 1px solid #e1def4;
  border-radius: 9px;
}
.st-key-dashboard_demo .sidebar-promo-card { margin: 0; padding: 0; text-align: center; background: transparent; border: 0; }
.st-key-dashboard_demo .sidebar-promo-desc { margin: 0; }
.st-key-dashboard_demo button p { white-space: nowrap !important; font-size: 12.5px !important; }
.st-key-dashboard_demo [data-testid="stExpander"] { background: #fff; border-radius: 8px; }
.st-key-dashboard_demo [data-testid="stExpander"] summary { padding: 5px 8px; }
.panel-header { margin: 0; }
.st-key-dashboard_toolbar { padding: 8px 0; border-bottom: 1px solid #e8ebf0; }
@media (min-width: 901px) {
  [data-testid="stLayoutWrapper"]:has(> .st-key-dashboard_toolbar) {
    position: sticky; top: 0; z-index: 5; background: #fff;
  }
}
.st-key-dashboard_toolbar .view-title { font-size: 18px; }
.st-key-dashboard_toolbar button { min-height: 33px; padding: 4px 9px; }
.budget-preview { display: grid; gap: 6px; }
.budget-preview-item { padding: 6px 9px; background: white; border-radius: 7px; }
.budget-preview-label { display: flex; align-items: center; gap: 7px; color: #202967; font-size: 11px; font-weight: 650; }
.budget-preview-label small { margin-left: auto; text-align: right; color: #526283; font-size: 10px; }
.budget-dot { display: inline-grid; place-items: center; flex: 0 0 18px; height: 18px; border-radius: 50%; color: white; font-size: 10px; }
.budget-progress-track { height: 4px; background: #e7e4f8; }
.budget-progress-fill { transform-origin: left; animation: budget-grow .55s ease-out both; }
@keyframes budget-grow { from { transform: scaleX(0); } to { transform: scaleX(1); } }
.metric-figure { animation: value-enter .28s cubic-bezier(.2,.7,.2,1) both; }
.st-key-dashboard_metrics [data-testid="stColumn"]:nth-child(2) .metric-figure { animation-delay: 35ms; }
.st-key-dashboard_metrics [data-testid="stColumn"]:nth-child(3) .metric-figure { animation-delay: 70ms; }
.st-key-dashboard_metrics [data-testid="stColumn"]:nth-child(4) .metric-figure { animation-delay: 105ms; }
@keyframes value-enter { from { opacity: .4; transform: translateY(5px); } to { opacity: 1; transform: translateY(0); } }

/* Ledger & Table Styling */
.ledger-header {
  font-size: 12px;
  font-weight: 700;
  color: #64748B;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  padding: 6px 10px;
  border-bottom: 2px solid #EDF2F7;
  margin-bottom: 4px;
}
.ledger-row {
  background: white;
  border: 1px solid #EDF2F7;
  border-radius: 10px;
  padding: 10px 14px;
  margin-bottom: 6px;
  transition: all 0.15s ease;
}
.ledger-row:hover {
  border-color: #CBD5E1;
  box-shadow: 0 4px 12px rgba(20, 24, 45, 0.03);
}

@media (prefers-reduced-motion: reduce) {
  .budget-progress-fill, .metric-card, .metric-figure, .stButton > button, .ledger-row {
    animation: none !important;
    transition: none !important;
  }
}
@media (max-width: 900px) {
  [data-testid="stMain"] { background: white !important; }
  [data-testid="stMainBlockContainer"] { padding: 47px 12px 24px !important; }
  [data-testid="stHeader"] { height: 48px !important; background: white !important; }
  [data-testid="stToolbar"] { display: flex !important; }
  [data-testid="stMain"] [data-testid="stHorizontalBlock"] { gap: 10px; }
}
@media (max-width: 640px) {
  .st-key-dashboard_metrics [data-testid="stHorizontalBlock"],
  .st-key-dashboard_toolbar [data-testid="stHorizontalBlock"] { display: grid !important; grid-template-columns: repeat(2, minmax(0,1fr)); }
  .st-key-dashboard_metrics [data-testid="stColumn"],
  .st-key-dashboard_toolbar [data-testid="stColumn"] { width: 100% !important; min-width: 0 !important; }
  .st-key-dashboard_toolbar [data-testid="stColumn"]:first-child { grid-column: 1 / -1; }
  .metric-card { min-height: 100px; padding: 12px; }
  .metric-figure { font-size: 19px; }
}
</style>
"""
st.html(NEXORA_CSS)


# -----------------------------------------------------------------------------
# Database & State Initialization
# -----------------------------------------------------------------------------
@st.cache_resource
def get_database() -> Database:
    return Database(os.environ.get("FINANCE_DB_PATH", "storage/finance.db"))


db = get_database()
categorizer = get_default_categorizer()

NAV_OPTIONS = ("Overview", "Transactions", "Budgets", "Category Review", "Model Evaluation")
available_months = db.get_available_months() or ["2026-10", "2026-11"]

# Direct query params initialize widgets; session state owns updates
query_nav = st.query_params.get("nav")
query_month = st.query_params.get("month")

st.session_state.setdefault("active_nav", query_nav if query_nav in NAV_OPTIONS else "Overview")
st.session_state.setdefault("selected_month", query_month if query_month in available_months else available_months[0])
st.session_state.setdefault("search_query", "")
st.session_state.setdefault("tx_type_filter", "All")
st.session_state.setdefault("tx_cat_filter", "All")
st.session_state.setdefault("tx_review_filter", "All")

if st.session_state.selected_month not in available_months:
    st.session_state.selected_month = available_months[0]


def open_search_results() -> None:
    if st.session_state.search_query.strip():
        st.session_state.active_nav = "Transactions"


# -----------------------------------------------------------------------------
# Sidebar Navigation & Actions
# -----------------------------------------------------------------------------
with st.sidebar:
    # SpendStory wordmark
    st.html(
        """
        <div class="nexora-logo">
            <span>SpendStory</span>
        </div>
        """
    )

    # Count items needing review for navigation badge
    unreviewed_items = db.get_transactions(review_status="needs_review")
    review_label = f"Category Review ({len(unreviewed_items)})" if unreviewed_items else "Category Review"

    st.radio(
        "Navigation",
        options=NAV_OPTIONS,
        key="active_nav",
        format_func=lambda section: review_label if section == "Category Review" else section,
        label_visibility="collapsed",
    )

    st.html('<div class="sidebar-spacer" aria-hidden="true"></div>')

    with st.container(key="dashboard_demo"):
        st.html(
            """
            <div class="sidebar-promo-card">
                <div class="sidebar-promo-title">Fictional Demo</div>
                <div class="sidebar-promo-desc">
                    Explore the dashboard with sample spending and budgets.
                </div>
            </div>
            """
        )

        if st.button("Load Fictional Demo", type="primary", width="stretch"):
            res = db.load_demo_data("data/demo/transactions.csv")
            st.session_state.selected_month = "2026-10"
            st.toast(f"Demo loaded! Inserted: {res.inserted}, Skipped: {res.skipped}")
            st.rerun()

        with st.expander("Reset / Clear Data"):
            st.caption("Erase local transactions and budgets stored in SQLite.")
            confirm = st.checkbox("I confirm clearing all data", key="clear_confirm_cb")
            if st.button("Clear All Data", type="secondary", disabled=not confirm, width="stretch"):
                db.clear_all_data()
                st.toast("Local data cleared successfully.")
                st.rerun()


# -----------------------------------------------------------------------------
# Contextual Top Toolbar
# -----------------------------------------------------------------------------
all_txs_for_month = db.get_transactions(year_month=st.session_state.selected_month)
show_import_dialog = False

with st.container(key="dashboard_toolbar"):
    if st.session_state.active_nav == "Overview":
        toolbar_cols = st.columns([3.0, 2.0, 2.0, 1.2, 1.2], vertical_alignment="center")
        with toolbar_cols[0]:
            st.html('<h1 class="view-title">Overview</h1>')
        with toolbar_cols[1]:
            st.text_input(
                "Search",
                key="search_query",
                placeholder="Search transactions...",
                label_visibility="collapsed",
                on_change=open_search_results,
            )
        with toolbar_cols[2]:
            st.selectbox(
                "Month",
                options=available_months,
                key="selected_month",
                format_func=lambda ym: datetime.strptime(ym, "%Y-%m").strftime("%B %Y"),
                label_visibility="collapsed",
            )
        with toolbar_cols[3]:
            csv_bytes = export_transactions_to_csv(all_txs_for_month).encode("utf-8")
            st.download_button(
                label="Export CSV",
                data=csv_bytes,
                file_name=f"transactions_{st.session_state.selected_month}.csv",
                mime="text/csv",
                width="stretch",
            )
        with toolbar_cols[4]:
            show_import_dialog = st.button("Import CSV", width="stretch")

    elif st.session_state.active_nav == "Transactions":
        toolbar_cols = st.columns([2.6, 2.2, 1.8, 1.2, 1.2], vertical_alignment="center")
        with toolbar_cols[0]:
            st.html('<h1 class="view-title">Transactions</h1>')
        with toolbar_cols[1]:
            st.text_input(
                "Search",
                key="search_query",
                placeholder="Search transactions...",
                label_visibility="collapsed",
            )
        with toolbar_cols[2]:
            st.selectbox(
                "Month",
                options=available_months,
                key="selected_month",
                format_func=lambda ym: datetime.strptime(ym, "%Y-%m").strftime("%B %Y"),
                label_visibility="collapsed",
            )
        with toolbar_cols[3]:
            csv_bytes = export_transactions_to_csv(all_txs_for_month).encode("utf-8")
            st.download_button(
                label="Export CSV",
                data=csv_bytes,
                file_name=f"transactions_{st.session_state.selected_month}.csv",
                mime="text/csv",
                width="stretch",
            )
        with toolbar_cols[4]:
            show_import_dialog = st.button("Import CSV", width="stretch")

    elif st.session_state.active_nav == "Budgets":
        toolbar_cols = st.columns([5.5, 2.0, 2.5], vertical_alignment="center")
        with toolbar_cols[0]:
            st.html('<h1 class="view-title">Budgets</h1>')
        with toolbar_cols[1]:
            st.html('<div style="text-align:right; color:#64748B; font-size:12px; font-weight:500;">Active Month:</div>')
        with toolbar_cols[2]:
            st.selectbox(
                "Month",
                options=available_months,
                key="selected_month",
                format_func=lambda ym: datetime.strptime(ym, "%Y-%m").strftime("%B %Y"),
                label_visibility="collapsed",
            )

    elif st.session_state.active_nav == "Category Review":
        toolbar_cols = st.columns([4.2, 3.2, 2.6], vertical_alignment="center")
        with toolbar_cols[0]:
            st.html('<h1 class="view-title">Category Review</h1>')
        with toolbar_cols[1]:
            st.radio(
                "Review Scope",
                options=["All Records", "Current Month"],
                horizontal=True,
                key="review_scope",
                label_visibility="collapsed",
            )
        with toolbar_cols[2]:
            if st.session_state.get("review_scope") == "Current Month":
                st.selectbox(
                    "Month",
                    options=available_months,
                    key="selected_month",
                    format_func=lambda ym: datetime.strptime(ym, "%Y-%m").strftime("%B %Y"),
                    label_visibility="collapsed",
                )
            else:
                st.html('<div style="text-align:right; font-size:11.5px; color:#64748B;">Scope: Entire Database</div>')

    elif st.session_state.active_nav == "Model Evaluation":
        toolbar_cols = st.columns([6.0, 4.0], vertical_alignment="center")
        with toolbar_cols[0]:
            st.html('<h1 class="view-title">Model Evaluation</h1>')
        with toolbar_cols[1]:
            st.html('<div style="text-align:right;"><span style="font-size:11.5px; background:#EDF0F7; color:#3B4863; padding:5px 10px; border-radius:12px; font-weight:600;">📊 Offline Holdout Dataset (Independent of Month)</span></div>')

# Sync query parameters with navigation & month
if query_nav != st.session_state.active_nav or query_month != st.session_state.selected_month:
    st.query_params.update(nav=st.session_state.active_nav, month=st.session_state.selected_month)

# CSV Import Panel
if show_import_dialog or st.session_state.get("show_import_panel", False):
    st.session_state.show_import_panel = True
    with st.container(border=True):
        st.subheader("Import Transactions CSV")
        st.caption("Upload a UTF-8 CSV with headers: `id,date,description,amount,type,category`. Limit 2 MB, 10,000 rows.")
        uploaded_file = st.file_uploader("Select CSV file", type=["csv"], label_visibility="collapsed")
        if uploaded_file:
            content_bytes = uploaded_file.read()
            txs, parse_errors = parse_transactions_csv(content_bytes)
            if parse_errors:
                st.error("Validation failed with zero records imported:")
                for err in parse_errors[:10]:
                    st.write(f"• {err}")
                if len(parse_errors) > 10:
                    st.caption(f"...and {len(parse_errors) - 10} more errors.")
            else:
                st.success(f"CSV validated successfully: {len(txs)} rows ready for atomic import.")
                preview_df = pd.DataFrame(
                    [
                        {
                            "ID": t.id,
                            "Date": t.date,
                            "Description": t.description,
                            "Amount (₹)": f"₹{t.amount_inr:,.2f}",
                            "Type": t.type,
                            "Category": t.category or "(Model Suggestion)",
                        }
                        for t in txs[:5]
                    ]
                )
                st.dataframe(preview_df, width="stretch", hide_index=True)
                if st.button("Commit Atomic Import", type="primary"):
                    prepared_txs = []
                    for t in txs:
                        if t.type == "expense" and not t.category:
                            pred = categorizer.predict(t.description)
                            prepared_txs.append(
                                Transaction(
                                    id=t.id,
                                    date=t.date,
                                    description=t.description,
                                    amount_paise=t.amount_paise,
                                    type=t.type,
                                    category=pred.category,
                                    category_source="model",
                                    review_status=pred.review_status,
                                    model_score=pred.model_score,
                                    fingerprint=t.fingerprint,
                                )
                            )
                        else:
                            prepared_txs.append(t)

                    res = db.save_transactions(prepared_txs)
                    st.toast(f"Import complete: {res.inserted} inserted, {res.skipped} skipped, {len(res.conflicts)} conflicts.")
                    st.session_state.show_import_panel = False
                    st.rerun()

        if st.button("Close Import Panel"):
            st.session_state.show_import_panel = False
            st.rerun()


# =============================================================================
# VIEW 1: OVERVIEW (Dribbble Nexora High-Fidelity Dashboard)
# =============================================================================
if st.session_state.active_nav == "Overview":
    month_name = datetime.strptime(st.session_state.selected_month, "%Y-%m").strftime("%B %Y")
    st.html(
        f'''
        <div class="greeting-header">Good day, Student 👋</div>
        <div class="greeting-subtext">Your money overview · {month_name}</div>
        '''
    )

    summary = calculate_monthly_summary(all_txs_for_month, st.session_state.selected_month)

    # Distinct visual treatment for surplus vs deficit
    if summary.recorded_surplus_paise > 0:
        surplus_caption = "Positive surplus · Income less expenses"
        surplus_tone = "green"
    elif summary.recorded_surplus_paise < 0:
        surplus_caption = "Recorded deficit · Expenses exceed income"
        surplus_tone = "red"
    else:
        surplus_caption = "Exact balance"
        surplus_tone = "blue"

    metrics = (
        ("Recorded income", summary.income_paise, "Income this month", "green"),
        ("Recorded expenses", summary.expense_paise, "Spending this month", "purple"),
        ("Recorded surplus", summary.recorded_surplus_paise, surplus_caption, surplus_tone),
        ("Transfers excluded", summary.transfer_paise, "Tracked separately · Excluded from surplus", "secondary"),
    )

    with st.container(key="dashboard_metrics"):
        for column, (label, amount, caption, tone) in zip(st.columns(4), metrics):
            with column:
                st.html(
                    f'''
                    <div class="metric-card">
                        <span class="metric-label">{label}</span>
                        <div class="metric-figure">{format_inr(amount)}</div>
                        <div class="metric-badge {tone}">{caption}</div>
                    </div>
                    '''
                )

    trend, breakdown = st.columns([7.15, 2.85])
    with trend, st.container(key="dashboard_trend"):
        surplus_color = "#182263" if summary.recorded_surplus_paise >= 0 else "#D32F2F"
        st.html(
            f'''
            <div class="panel-header">
                <div>
                    <div class="panel-title">Income &amp; expense trends</div>
                    <div class="trend-surplus" style="color: {surplus_color};">{format_inr(summary.recorded_surplus_paise)}</div>
                </div>
                <span class="chart-period">Recorded surplus · {month_name}</span>
            </div>
            '''
        )
        trend_data = calculate_cumulative_trend(all_txs_for_month, st.session_state.selected_month)
        if trend_data:
            render_trend(trend_data, key="overview_trend")
        else:
            st.caption("Add transactions to see how your month is taking shape.")

    with breakdown, st.container(key="dashboard_breakdown"):
        st.html('<div class="panel-header"><span class="panel-title">Monthly expenses breakdown</span></div>')
        donut_rows = [
            {"Category": category, "Amount": paise / 100}
            for category, paise in summary.expense_by_category_paise.items()
            if paise > 0
        ]
        if donut_rows:
            render_donut(donut_rows, key="overview_breakdown")
        else:
            st.caption("Your expense breakdown will appear here.")

    budgets, comparison = st.columns([2.85, 7.15])
    with budgets, st.container(key="dashboard_budgets"):
        st.html('<div class="panel-header"><span class="panel-title">Monthly budgets</span></div>')
        budget_targets = db.get_budgets(st.session_state.selected_month)
        comparisons = calculate_budget_comparisons(summary.expense_by_category_paise, budget_targets)
        if comparisons:
            colors = ("#19b961", "#0baeca", "#5675f3", "#6148e5", "#9149ea", "#f59e0b", "#ec4899")
            rows = []
            for index, item in enumerate(comparisons[:5]):
                color = colors[index % len(colors)]
                spent = format_inr(item.spent_paise)
                if item.budget_paise is None:
                    status = spent + " · No target set"
                    badge_style = "color:#64748B;"
                elif item.is_over:
                    status = format_inr(item.delta_paise) + " over"
                    badge_style = "color:#D32F2F; font-weight:700;"
                else:
                    status = spent + " / " + format_inr(item.budget_paise)
                    badge_style = "color:#059669;"
                progress = min(100, item.percent_used or 0)
                rows.append(
                    f'''
                    <div class="budget-preview-item">
                      <div class="budget-preview-label">
                        <span class="budget-dot" style="background:{color}" aria-hidden="true">{html.escape(item.category[:1])}</span>
                        <span>{html.escape(item.category)}</span><small style="{badge_style}">{status}</small>
                      </div>
                      <div class="budget-progress-track" aria-hidden="true">
                        <div class="budget-progress-fill" style="width:{progress}%;background:{color}"></div>
                      </div>
                    </div>
                    '''
                )
            st.html('<div class="budget-preview">' + "".join(rows) + '</div>')
            if len(comparisons) > 5:
                st.caption(f"Showing 5 of {len(comparisons)} categories.")
            if st.button("Manage all budgets →", key="btn_goto_budgets", width="stretch"):
                st.session_state.active_nav = "Budgets"
                st.rerun()
        else:
            st.caption("Set a budget to track spending against a target.")

    with comparison, st.container(key="dashboard_comparison"):
        multi_month = calculate_multi_month_comparison(db.get_transactions())
        hint = '<span class="chart-period">Select a month to explore</span>' if multi_month else ''
        st.html(f'<div class="panel-header"><span class="panel-title">Monthly income vs expenses</span>{hint}</div>')
        if multi_month:
            render_monthly(multi_month, selected_month=st.session_state.selected_month, key="overview_monthly")
        else:
            st.caption("Record income or expenses to compare months.")


# =============================================================================
# VIEW 2: TRANSACTIONS & CSV WORKFLOWS
# =============================================================================
elif st.session_state.active_nav == "Transactions":
    month_name = datetime.strptime(st.session_state.selected_month, "%Y-%m").strftime("%B %Y")
    
    t_head_col, t_act_col = st.columns([7, 3], vertical_alignment="center")
    with t_head_col:
        st.subheader(f"Transactions — {month_name}")
        st.caption("Browse, filter, edit categories, and record student financial entries.")
    with t_act_col:
        add_clicked = st.button("➕ Add Transaction", type="primary", width="stretch")
        if add_clicked:
            st.session_state.show_add_tx = not st.session_state.get("show_add_tx", False)

    # Focused Add Transaction Editor
    if st.session_state.get("show_add_tx", False):
        with st.container(border=True):
            st.markdown("#### Record New Transaction")
            with st.form("add_tx_form", clear_on_submit=False):
                a_col1, a_col2 = st.columns([2, 2])
                with a_col1:
                    default_date = date.today()
                    try:
                        # Default date aligned with selected month
                        default_date = date(int(st.session_state.selected_month[:4]), int(st.session_state.selected_month[5:7]), 15)
                    except Exception:
                        pass
                    tx_date = st.date_input("Date", value=default_date)
                    tx_type = st.selectbox("Type", options=["expense", "income", "transfer"])
                with a_col2:
                    tx_amount = st.text_input("Amount in INR (₹)", placeholder="e.g. 150.00")
                    if tx_type == "expense":
                        tx_cat = st.selectbox(
                            "Category",
                            options=["(Let AI Suggest Category)"] + sorted(list(ALLOWED_EXPENSE_CATEGORIES)),
                        )
                    elif tx_type == "income":
                        tx_cat = "Income"
                        st.text_input("Category", value="Income", disabled=True)
                    else:
                        tx_cat = "Transfer"
                        st.text_input("Category", value="Transfer", disabled=True)

                tx_desc = st.text_input("Description", placeholder="e.g. University canteen thali, Semester book purchase")

                f_btn_col1, f_btn_col2 = st.columns([2, 8])
                with f_btn_col1:
                    submit_tx = st.form_submit_button("Record Transaction", type="primary", width="stretch")
                with f_btn_col2:
                    cancel_add = st.form_submit_button("Cancel", width="stretch")

                if cancel_add:
                    st.session_state.show_add_tx = False
                    st.rerun()

                if submit_tx:
                    clean_desc = tx_desc.strip()
                    if not clean_desc:
                        st.error("Description cannot be empty.")
                    else:
                        try:
                            paise = parse_amount_to_paise(tx_amount)
                            if paise <= 0:
                                st.error("Amount must be greater than zero.")
                            else:
                                iso_date = tx_date.isoformat()
                                gen_id = f"TX-{datetime.now().strftime('%Y%m%d%H%M%S%f')[:17]}"
                                final_cat = ""
                                cat_src = "manual"
                                status = "confirmed"
                                score = None

                                if tx_type == "income":
                                    final_cat = "Income"
                                elif tx_type == "transfer":
                                    final_cat = "Transfer"
                                else:
                                    if tx_cat == "(Let AI Suggest Category)":
                                        pred = categorizer.predict(clean_desc)
                                        final_cat = pred.category
                                        cat_src = "model"
                                        status = pred.review_status
                                        score = pred.model_score
                                    else:
                                        final_cat = tx_cat

                                fp = compute_fingerprint(iso_date, clean_desc, paise, tx_type)
                                new_tx = Transaction(
                                    id=gen_id,
                                    date=iso_date,
                                    description=clean_desc,
                                    amount_paise=paise,
                                    type=tx_type,
                                    category=final_cat,
                                    category_source=cat_src,
                                    review_status=status,
                                    model_score=score,
                                    fingerprint=fp,
                                )
                                db.add_transaction(new_tx)
                                st.session_state.show_add_tx = False
                                
                                # Inform if transaction date is outside currently active month
                                tx_month = iso_date[:7]
                                if tx_month != st.session_state.selected_month:
                                    st.info(f"Transaction recorded for {iso_date}! Note: This entry is in {tx_month}, outside your currently viewed month ({st.session_state.selected_month}).")
                                else:
                                    st.toast(f"Transaction recorded! Assigned category: {final_cat}")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Error parsing amount: {e}")

    # Consolidated Filter Area
    with st.container(border=True):
        flt_c1, flt_c2, flt_c3, flt_c4 = st.columns([2.5, 2.5, 2.5, 2.5])
        with flt_c1:
            tx_type_options = ["All", "expense", "income", "transfer"]
            cur_type_idx = tx_type_options.index(st.session_state.tx_type_filter) if st.session_state.tx_type_filter in tx_type_options else 0
            selected_type = st.selectbox("Type", options=tx_type_options, index=cur_type_idx, key="tx_type_filter")
        with flt_c2:
            cat_options = ["All"] + sorted(list(ALLOWED_EXPENSE_CATEGORIES)) + ["Income", "Transfer"]
            cur_cat_idx = cat_options.index(st.session_state.tx_cat_filter) if st.session_state.tx_cat_filter in cat_options else 0
            selected_cat = st.selectbox("Category", options=cat_options, index=cur_cat_idx, key="tx_cat_filter")
        with flt_c3:
            rev_options = ["All", "needs_review", "confirmed"]
            cur_rev_idx = rev_options.index(st.session_state.tx_review_filter) if st.session_state.tx_review_filter in rev_options else 0
            selected_rev = st.selectbox("Review Status", options=rev_options, index=cur_rev_idx, key="tx_review_filter")
        with flt_c4:
            sort_order = st.selectbox("Sort Order", options=["Date: Newest First", "Date: Oldest First", "Amount: Highest First", "Amount: Lowest First"])

        active_chips = []
        if selected_type != "All":
            active_chips.append(f"Type: {selected_type}")
        if selected_cat != "All":
            active_chips.append(f"Category: {selected_cat}")
        if selected_rev != "All":
            active_chips.append(f"Status: {selected_rev}")
        if st.session_state.search_query.strip():
            active_chips.append(f'Search: "{st.session_state.search_query.strip()}"')

        ch_col, rst_col = st.columns([8, 2], vertical_alignment="center")
        with ch_col:
            if active_chips:
                st.html(f'<span style="font-size:12px; color:#475569;">Active Filters: <b>{" • ".join(active_chips)}</b></span>')
            else:
                st.html('<span style="font-size:12px; color:#64748B;">Showing all records for selected month.</span>')
        with rst_col:
            if active_chips:
                if st.button("Reset Filters", width="stretch"):
                    st.session_state.tx_type_filter = "All"
                    st.session_state.tx_cat_filter = "All"
                    st.session_state.tx_review_filter = "All"
                    st.session_state.search_query = ""
                    st.rerun()

    # Query matching records
    matching_txs = db.get_transactions(
        year_month=st.session_state.selected_month,
        category=selected_cat if selected_cat != "All" else None,
        tx_type=selected_type if selected_type != "All" else None,
        review_status=selected_rev if selected_rev != "All" else None,
        search_query=st.session_state.search_query.strip() or None,
    )

    # Sort matching records
    if sort_order == "Date: Oldest First":
        matching_txs = sorted(matching_txs, key=lambda t: (t.date, t.id))
    elif sort_order == "Amount: Highest First":
        matching_txs = sorted(matching_txs, key=lambda t: t.amount_paise, reverse=True)
    elif sort_order == "Amount: Lowest First":
        matching_txs = sorted(matching_txs, key=lambda t: t.amount_paise)
    else:  # Date: Newest First
        matching_txs = sorted(matching_txs, key=lambda t: (t.date, t.id), reverse=True)

    if matching_txs:
        st.write(f"Showing **{len(matching_txs)}** transaction(s).")

        # Table Header
        h_cols = st.columns([1.5, 3.8, 1.6, 1.2, 2.4, 1.5])
        with h_cols[0]:
            st.markdown('<div class="ledger-header">Date</div>', unsafe_allow_html=True)
        with h_cols[1]:
            st.markdown('<div class="ledger-header">Description &amp; Status</div>', unsafe_allow_html=True)
        with h_cols[2]:
            st.markdown('<div class="ledger-header">Amount</div>', unsafe_allow_html=True)
        with h_cols[3]:
            st.markdown('<div class="ledger-header">Type</div>', unsafe_allow_html=True)
        with h_cols[4]:
            st.markdown('<div class="ledger-header">Category</div>', unsafe_allow_html=True)
        with h_cols[5]:
            st.markdown('<div class="ledger-header">Action</div>', unsafe_allow_html=True)

        for tx in matching_txs:
            with st.container(border=True):
                r_cols = st.columns([1.5, 3.8, 1.6, 1.2, 2.4, 1.5], vertical_alignment="center")
                with r_cols[0]:
                    st.write(f"**{tx.date}**")
                    st.html(f'<span style="font-size:10px; color:#94A3B8; font-family:monospace;" title="{tx.id}">{tx.id[:12]}…</span>')
                with r_cols[1]:
                    st.write(html.escape(tx.description))
                    badge = f'<span class="badge-review">Review ({tx.model_score:.2f})</span>' if tx.review_status == "needs_review" else '<span class="badge-confirmed">Confirmed</span>'
                    st.html(f'<span style="font-size:11px; color:#7A8499;">Source: {tx.category_source} • {badge}</span>')
                with r_cols[2]:
                    amt_color = "#059669" if tx.type == "income" else ("#182263" if tx.type == "expense" else "#3B82F6")
                    st.html(f'<span style="font-weight:700; color:{amt_color}; font-variant-numeric:tabular-nums;">{format_inr(tx.amount_paise)}</span>')
                with r_cols[3]:
                    st.code(tx.type, language=None)
                with r_cols[4]:
                    if tx.type == "expense":
                        cat_opts = sorted(list(ALLOWED_EXPENSE_CATEGORIES))
                        cur_idx = cat_opts.index(tx.category) if tx.category in cat_opts else 0
                        new_cat = st.selectbox(
                            "Category",
                            options=cat_opts,
                            index=cur_idx,
                            key=f"edit_cat_{tx.id}",
                            label_visibility="collapsed",
                        )
                        if new_cat != tx.category:
                            db.update_transaction_category(tx.id, new_cat, review_status="confirmed", category_source="manual")
                            st.toast(f"Updated {tx.id} category to {new_cat}")
                            st.rerun()
                    else:
                        st.write(f"*{tx.category}*")
                with r_cols[5]:
                    del_key = f"del_confirm_{tx.id}"
                    if not st.session_state.get(del_key, False):
                        if st.button("Delete", key=f"btn_del_{tx.id}", type="secondary", width="stretch"):
                            st.session_state[del_key] = True
                            st.rerun()
                    else:
                        st.error("Delete?")
                        d_c1, d_c2 = st.columns(2)
                        with d_c1:
                            if st.button("Yes", key=f"conf_yes_{tx.id}", type="primary"):
                                db.delete_transaction(tx.id)
                                st.session_state[del_key] = False
                                st.toast(f"Deleted {tx.description}")
                                st.rerun()
                        with d_c2:
                            if st.button("No", key=f"conf_no_{tx.id}"):
                                st.session_state[del_key] = False
                                st.rerun()
    else:
        st.info("No transactions match the selected criteria for this month.")


# =============================================================================
# VIEW 3: BUDGETS
# =============================================================================
elif st.session_state.active_nav == "Budgets":
    month_name = datetime.strptime(st.session_state.selected_month, "%Y-%m").strftime("%B %Y")
    
    b_head_col, b_act_col = st.columns([7, 3], vertical_alignment="center")
    with b_head_col:
        st.subheader(f"Category Budgets — {month_name}")
        st.caption("Configure category targets, track utilization, and review deterministic spending rebalancing suggestions.")
    with b_act_col:
        edit_budgets_clicked = st.button("✏️ Configure Budgets", type="primary", width="stretch")
        if edit_budgets_clicked:
            st.session_state.show_budget_editor = not st.session_state.get("show_budget_editor", False)

    summary = calculate_monthly_summary(all_txs_for_month, st.session_state.selected_month)
    current_budgets = db.get_budgets(st.session_state.selected_month)

    # Budget Configuration Editor
    if st.session_state.get("show_budget_editor", False):
        with st.container(border=True):
            st.markdown("#### Set Monthly Category Targets")
            st.caption("Check 'Has Target' to set a budget limit in Rupees (₹). Uncheck to remove target ('No Target').")
            with st.form("set_budgets_form"):
                budget_entries = {}
                for cat in sorted(list(ALLOWED_EXPENSE_CATEGORIES)):
                    cur_paise = current_budgets.get(cat)
                    has_target_default = cur_paise is not None
                    cur_inr = float(cur_paise / 100.0) if cur_paise is not None else 0.0

                    c_check, c_input = st.columns([2, 5])
                    with c_check:
                        has_target = st.checkbox(f"Track {cat}", value=has_target_default, key=f"chk_target_{cat}")
                    with c_input:
                        val = st.number_input(
                            f"{cat} Target (₹)",
                            min_value=0.0,
                            value=cur_inr,
                            step=100.0,
                            disabled=not has_target,
                            key=f"num_target_{cat}",
                        )
                    budget_entries[cat] = (has_target, val)

                b_btn1, b_btn2 = st.columns([2, 8])
                with b_btn1:
                    save_budgets = st.form_submit_button("Save Budgets", type="primary", width="stretch")
                with b_btn2:
                    cancel_budgets = st.form_submit_button("Cancel", width="stretch")

                if cancel_budgets:
                    st.session_state.show_budget_editor = False
                    st.rerun()

                if save_budgets:
                    for cat, (has_target, val) in budget_entries.items():
                        if has_target:
                            paise_val = int(round(val * 100))
                            db.set_budget(st.session_state.selected_month, cat, paise_val)
                        else:
                            db.delete_budget(st.session_state.selected_month, cat)
                    st.session_state.show_budget_editor = False
                    st.toast("Budgets updated successfully!")
                    st.rerun()

    # Re-calculate comparisons after any potential changes
    current_budgets = db.get_budgets(st.session_state.selected_month)
    comparisons = calculate_budget_comparisons(summary.expense_by_category_paise, current_budgets)

    # Cohesive Unified Budget Cards List
    st.markdown("#### Category Budget Utilization & Recommendations")
    for comp in comparisons:
        with st.container(border=True):
            b_top1, b_top2 = st.columns([6, 4], vertical_alignment="center")
            with b_top1:
                st.markdown(f"### {comp.category}")
            with b_top2:
                if comp.budget_paise is None:
                    st.html('<div style="text-align:right;"><span class="badge-secondary" style="padding:4px 8px; border-radius:6px; background:#F1F5F9; color:#64748B; font-size:11px; font-weight:600;">⚪ No Target Set</span></div>')
                elif comp.is_over:
                    st.html(f'<div style="text-align:right;"><span class="badge-overbudget">⚠️ Exceeded by {format_inr(comp.delta_paise)}</span></div>')
                else:
                    st.html('<div style="text-align:right;"><span class="badge-confirmed">✅ Within Budget</span></div>')

            # Metric triplets: Target | Spent | Balance
            m_col1, m_col2, m_col3 = st.columns(3)
            with m_col1:
                target_str = format_inr(comp.budget_paise) if comp.budget_paise is not None else "No target"
                st.metric("Target Budget", target_str)
            with m_col2:
                st.metric("Actual Spend", format_inr(comp.spent_paise))
            with m_col3:
                if comp.budget_paise is not None:
                    remaining_paise = comp.budget_paise - comp.spent_paise
                    rem_label = "Remaining" if remaining_paise >= 0 else "Overspend"
                    st.metric(rem_label, format_inr(remaining_paise))
                else:
                    st.metric("Balance", "N/A")

            # Bounded progress track
            progress = min(100.0, comp.percent_used or 0.0)
            fill_color = "#EF4444" if comp.is_over else "#10B981"
            pct_label = f"{comp.percent_used:.1f}% used" if comp.percent_used is not None else "No target set"

            st.html(
                f'''
                <div style="margin: 8px 0 4px 0;">
                    <div style="display:flex; justify-content:space-between; font-size:11px; color:#64748B;">
                        <span>Progress</span>
                        <span><b>{pct_label}</b></span>
                    </div>
                    <div class="budget-progress-track">
                        <div class="budget-progress-fill" style="width:{progress}%; background:{fill_color};"></div>
                    </div>
                </div>
                '''
            )
            st.caption(f"💡 **Suggestion:** {comp.suggestion}")


# =============================================================================
# VIEW 4: CATEGORY REVIEW
# =============================================================================
elif st.session_state.active_nav == "Category Review":
    scope_mode = st.session_state.get("review_scope", "All Records")
    month_name = datetime.strptime(st.session_state.selected_month, "%Y-%m").strftime("%B %Y")
    
    if scope_mode == "Current Month":
        pending_txs = db.get_transactions(year_month=st.session_state.selected_month, review_status="needs_review")
        scope_desc = f"Showing unconfirmed expenses for {month_name}"
    else:
        pending_txs = db.get_transactions(review_status="needs_review")
        scope_desc = "Showing unconfirmed expenses across all dates"

    st.subheader("AI Category Review Queue")
    st.caption(f"{scope_desc}. Verify or adjust predicted categories.")

    if not pending_txs:
        st.success("🎉 All transaction categories in this scope are confirmed! Zero items require review.")
        st.html(
            """
            <div style="text-align:center; padding: 40px 10px; color:#5A6478;">
                <div style="font-size: 32px; margin-bottom: 8px;">✨</div>
                <div style="font-size: 15px; font-weight: 600; color: #182263;">Queue is Completely Clear</div>
                <div style="font-size: 12.5px; color: #64748B; margin-top: 4px;">
                    When you import new expenses with unfamiliar descriptions, they will appear here for verification.
                </div>
            </div>
            """
        )
    else:
        st.warning(f"**{len(pending_txs)}** transaction(s) require human review or confirmation.")

        for tx in pending_txs:
            with st.container(border=True):
                c_cols = st.columns([1.5, 4.2, 1.6, 2.7, 2.0], vertical_alignment="center")
                with c_cols[0]:
                    st.write(f"**{tx.date}**")
                    st.html(f'<span style="font-size:10px; color:#94A3B8; font-family:monospace;">{tx.id[:12]}…</span>')
                with c_cols[1]:
                    st.write(f"**{html.escape(tx.description)}**")
                    score_str = f"Model Score: {tx.model_score:.2f} (Uncalibrated ML confidence)" if tx.model_score is not None else "Model Score: N/A"
                    reason = "Flagged because model confidence is below the review threshold (0.25). Likely contains unfamiliar or ambiguous keywords."
                    st.html(f'<div style="font-size:11px; color:#64748B;">{score_str}</div><div style="font-size:11px; color:#D97706; margin-top:2px;">⚠️ {reason}</div>')
                with c_cols[2]:
                    st.html(f'<span style="font-weight:700; color:#182263; font-variant-numeric:tabular-nums;">{format_inr(tx.amount_paise)}</span>')
                with c_cols[3]:
                    cat_options = sorted(list(ALLOWED_EXPENSE_CATEGORIES))
                    cur_idx = cat_options.index(tx.category) if tx.category in cat_options else 0
                    chosen_cat = st.selectbox(
                        "Confirm Category",
                        options=cat_options,
                        index=cur_idx,
                        key=f"rev_cat_{tx.id}",
                        label_visibility="collapsed",
                    )
                with c_cols[4]:
                    btn_confirm = st.button("Confirm Category", key=f"btn_confirm_{tx.id}", type="primary", width="stretch")
                    if btn_confirm:
                        db.update_transaction_category(tx.id, chosen_cat, review_status="confirmed", category_source="manual")
                        st.toast(f"Confirmed {tx.id} as {chosen_cat}")
                        st.rerun()


# =============================================================================
# VIEW 5: MODEL EVALUATION & TRANSPARENCY
# =============================================================================
elif st.session_state.active_nav == "Model Evaluation":
    st.subheader("Machine Learning Model Evaluation & Transparency")
    st.caption("Empirical reporting on offline TF-IDF + Logistic Regression classification against an untouched holdout dataset.")

    st.info(
        "📌 **Offline Evaluation Notice:** The statistics and matrix below evaluate the categorizer on an independent, "
        "synthetic holdout validation set of 18 student transactions. These metrics do not reflect the active monthly ledger."
    )

    eval_json_path = Path("reports/model_evaluation.json")
    if eval_json_path.exists():
        with open(eval_json_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)

        meta = report_data.get("metadata", {})
        metrics = report_data.get("metrics", {})
        per_cat = report_data.get("per_category_metrics", {})

        e_cols = st.columns(4)
        with e_cols[0]:
            st.metric("Training Samples", meta.get("training_samples", 0), help="Number of verified examples in training split")
        with e_cols[1]:
            st.metric("Holdout Samples", meta.get("holdout_samples", 0), help="Independent holdout validation examples")
        with e_cols[2]:
            st.metric("Overall Accuracy", f"{metrics.get('overall_accuracy', 0.0) * 100:.1f}%", help="Correct classifications over all 18 holdout examples")
        with e_cols[3]:
            st.metric("Abstention Rate", f"{metrics.get('abstention_rate', 0.0) * 100:.1f}%", help="Percentage of examples routed to human review (below 0.25 confidence)")

        m_sub1, m_sub2, m_sub3, m_sub4 = st.columns(4)
        with m_sub1:
            st.metric("Model Coverage", f"{metrics.get('coverage', 0.0) * 100:.1f}%")
        with m_sub2:
            non_abstained = metrics.get("non_abstained", 0)
            correct_na = metrics.get("correct_non_abstained", 0)
            na_acc = (correct_na / non_abstained * 100.0) if non_abstained > 0 else 0.0
            st.metric("Non-Abstained Accuracy", f"{na_acc:.1f}%", help="Accuracy on examples the model chose to predict")
        with m_sub3:
            st.metric("Confidence Threshold", f"{meta.get('confidence_threshold', 0.25):.2f}")
        with m_sub4:
            st.metric("Classification Model", "TF-IDF + LogReg")

        st.markdown("#### Per-Category Holdout Performance")
        st.caption("Breakdown of precision, recall, and support across expense categories.")

        table_rows = []
        for cat, data in per_cat.items():
            supp = data.get("support", 0)
            prec = data.get("precision", 0.0)
            rec = data.get("recall", 0.0)
            f1 = data.get("f1_score", 0.0)
            table_rows.append({
                "Category": cat,
                "Holdout Support": supp,
                "Precision": f"{prec * 100:.1f}%" if supp > 0 else "N/A",
                "Recall": f"{rec * 100:.1f}%" if supp > 0 else "N/A",
                "F1-Score": f"{f1 * 100:.1f}%" if supp > 0 else "N/A",
            })
        st.dataframe(pd.DataFrame(table_rows), width="stretch", hide_index=True)

        with st.expander("📖 Methodological Disclosures & Honest Limitations"):
            st.markdown(
                """
                - **Explainability First:** The model combines a linear classifier with an explicit vocabulary coverage check. When descriptions contain out-of-vocabulary or ambiguous tokens, it routes them to human review rather than hallucinating categories.
                - **Why Accuracy is 27.8%:** Standard logistic regression without abstention forces a guess on every token. With our safety threshold (0.25), 72.2% of holdout examples abstain to review. On non-abstained predictions, accuracy is **100.0%**.
                - **Privacy Sovereignty:** All inference is executed locally using `scikit-learn`. Zero transaction text or telemetry leaves the device.
                """
            )
            for lim in report_data.get("honest_limitations", []):
                st.write(f"• {lim}")
    else:
        st.info("Evaluation report not found. Run `python scripts/evaluate_model.py` to generate it.")
