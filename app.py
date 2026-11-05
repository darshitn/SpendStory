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
    validate_transaction_row,
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
    font-size: 13.5px !important;
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
    font-size: 24px;
    font-weight: 700;
    color: #14182D;
    letter-spacing: -0.5px;
    margin-bottom: 2px;
}

.greeting-subtext {
    font-size: 13px;
    color: #8E95A9;
    font-weight: 400;
    margin-bottom: 20px;
}

/* Four Equal Financial Summary Cards */
.metric-card {
    background-color: #F8FAFD;
    border: 1px solid #EAEFF7;
    border-radius: 16px;
    padding: 18px 20px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    height: 118px;
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
    font-size: 26px;
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
}

.metric-badge.purple {
    color: #7E3AF2;
}

.metric-badge.blue {
    color: #373EDC;
}

/* Chart panel headings */
.panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
}

.panel-title {
    font-size: 15px;
    font-weight: 700;
    color: #14182D;
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
    background-color: #FDE8E8;
    color: #9B1C1C;
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
    border-radius: 16px;
    padding: 16px;
    margin-top: 24px;
}

.sidebar-promo-title {
    font-size: 13px;
    font-weight: 700;
    color: #14182D;
    margin-bottom: 4px;
}

.sidebar-promo-desc {
    font-size: 11.5px;
    color: #5A6478;
    line-height: 1.4;
    margin-bottom: 12px;
}

/* Streamlit 1.66: the app view is the common parent of sidebar and main. */
@media (min-width: 901px) {
  [data-testid="stAppViewContainer"] {
    --frame-gutter: clamp(20px, 2.2vw, 42px);
    --frame-top: clamp(18px, 2.8vh, 32px);
    --rail: clamp(166px, 13.4vw, 222px);
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
[data-testid="stMainBlockContainer"] { max-width: none !important; padding: 0 14px 16px !important; }
[data-testid="stSidebar"] { padding-top: 0 !important; background: #f3f6f8 !important; }
[data-testid="stSidebar"] [data-testid="stSidebarContent"] { padding: 0 !important; }
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] { padding: 0 13px 14px !important; min-height: 100%; }
[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] > [data-testid="stVerticalBlock"] { min-height: 100%; }
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] > [data-testid="stElementContainer"]:has(.sidebar-spacer) { flex: 1; min-height: 12px; }
[data-testid="stSidebar"] [data-testid="stVerticalBlock"] { gap: .55rem !important; }
[data-testid="stSidebar"] .stRadio [role="radiogroup"] { gap: 3px !important; }
[data-testid="stSidebar"] .stRadio label { padding: 8px 10px !important; width: 100%; }
[data-testid="stSidebar"] .stRadio label:has(input:checked) { background: #e9eafd; color: #3029c5 !important; }
[data-testid="stRadioOption"] > div > div:first-child { display: none; }
[data-testid="stSidebar"] .stRadio label:focus-within { outline: 2px solid #373edc; outline-offset: 2px; }
[data-testid="stSidebar"] .stRadio label p { display: flex; align-items: center; gap: 9px; font-size: 13px; }
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
  background: #f3f5f7; border: 1px solid #edf0f4; border-radius: 10px; padding: 12px !important;
}
.trend-surplus { line-height: 1.2; margin-top: 4px; color: #182263; font-size: 28px; font-weight: 750; letter-spacing: -.7px; }
.chart-period { color: #586889; font-size: 10.5px; text-align: right; }
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
.st-key-dashboard_demo [data-testid="stExpander"] { background: #fff; border-radius: 8px; }
.st-key-dashboard_demo [data-testid="stExpander"] summary { padding: 5px 8px; }
.greeting-header { font-size: 18px; color: #182263; }
.greeting-subtext { margin-bottom: 2px; color: #586889; font-size: 12px; }
.metric-card { height: 108px; padding: 12px 13px; border-radius: 9px; background: #f3f5f7; }
.metric-figure { font-size: clamp(17px, 1.75vw, 27px); }
.panel-header { margin: 0; }
.panel-title { font-size: 13px; color: #182263; }
.st-key-dashboard_toolbar { padding: 6px 0; border-bottom: 1px solid #e8ebf0; }
@media (min-width: 901px) {
  [data-testid="stLayoutWrapper"]:has(> .st-key-dashboard_toolbar) {
    position: sticky; top: 0; z-index: 5; background: #fff;
  }
}
.st-key-dashboard_toolbar .view-title { font-size: 17px; }
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
@media (prefers-reduced-motion: reduce) {
  .budget-progress-fill, .metric-card, .metric-figure, .stButton > button { animation: none !important; transition: none !important; }
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
  .metric-card { height: 100px; }
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

# A direct link initializes the widgets. Their keyed values own subsequent changes.
query_nav = st.query_params.get("nav")
query_month = st.query_params.get("month")
st.session_state.setdefault("active_nav", query_nav if query_nav in NAV_OPTIONS else "Overview")
st.session_state.setdefault("selected_month", query_month if query_month in available_months else available_months[0])
st.session_state.setdefault("search_query", "")

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
        # Sidebar Action Card (Replacing 'Upgrade to Pro' with Fictional Demo loader)
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
# Global Top Toolbar
# -----------------------------------------------------------------------------
with st.container(key="dashboard_toolbar"):
    toolbar_cols = st.columns([2.6, 2, 1.8, 1.1, 1.1], vertical_alignment="center")

    with toolbar_cols[0]:
        st.html(f'<h1 class="view-title">{st.session_state.active_nav}</h1>')

    with toolbar_cols[1]:
        st.text_input(
            "Search",
            key="search_query",
            placeholder="Search transactions",
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

    all_txs_for_month = db.get_transactions(year_month=st.session_state.selected_month)

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

if query_nav != st.session_state.active_nav or query_month != st.session_state.selected_month:
    st.query_params.update(nav=st.session_state.active_nav, month=st.session_state.selected_month)

# Optional CSV Import Staging Expander
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
                    # For transactions with empty categories, predict using AI
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
    metrics = (
        ("Recorded income", summary.income_paise, "Income this month", "green"),
        ("Recorded expenses", summary.expense_paise, "Spending this month", "purple"),
        ("Recorded surplus", summary.recorded_surplus_paise, "Income less expenses",
         "green" if summary.recorded_surplus_paise >= 0 else "purple"),
        ("Transfers excluded", summary.transfer_paise, "Moves between accounts", "blue"),
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
        st.html(
            f'''
            <div class="panel-header">
                <div>
                    <div class="panel-title">Income &amp; expense trends</div>
                    <div class="trend-surplus">{format_inr(summary.recorded_surplus_paise)}</div>
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
            colors = ("#19b961", "#0baeca", "#5675f3", "#6148e5", "#9149ea")
            rows = []
            for index, item in enumerate(comparisons[:5]):
                color = colors[index]
                spent = format_inr(item.spent_paise)
                if item.budget_paise is None:
                    status = spent + " · No target"
                elif item.is_over:
                    status = format_inr(item.delta_paise) + " over"
                else:
                    status = spent + " / " + format_inr(item.budget_paise)
                progress = min(100, item.percent_used or 0)
                rows.append(
                    f'''
                    <div class="budget-preview-item">
                      <div class="budget-preview-label">
                        <span class="budget-dot" style="background:{color}" aria-hidden="true">{html.escape(item.category[:1])}</span>
                        <span>{html.escape(item.category)}</span><small>{status}</small>
                      </div>
                      <div class="budget-progress-track" aria-hidden="true">
                        <div class="budget-progress-fill" style="width:{progress}%;background:{color}"></div>
                      </div>
                    </div>
                    '''
                )
            st.html('<div class="budget-preview">' + "".join(rows) + '</div>')
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
# VIEW 2: TRANSACTIONS
# =============================================================================
elif st.session_state.active_nav == "Transactions":
    st.subheader(f"Transactions — {datetime.strptime(st.session_state.selected_month, '%Y-%m').strftime('%B %Y')}")
    st.caption("Browse, search, edit categories, and record student financial entries.")

    # Top Filters & Add Transaction Expander
    f_cols = st.columns([2, 2, 3])
    with f_cols[0]:
        type_filter = st.selectbox("Type", options=["All", "income", "expense", "transfer"])
    with f_cols[1]:
        cat_filter = st.selectbox("Category", options=["All"] + sorted(list(ALLOWED_EXPENSE_CATEGORIES)) + ["Income", "Transfer"])

    with st.expander("➕ Add New Transaction"):
        with st.form("add_tx_form", clear_on_submit=True):
            a_cols = st.columns([1.5, 3, 1.5, 1.5, 2])
            with a_cols[0]:
                tx_date = st.date_input("Date", value=date.today())
            with a_cols[1]:
                tx_desc = st.text_input("Description", placeholder="e.g. Canteen lunch or Bus fare")
            with a_cols[2]:
                tx_amount = st.text_input("Amount (₹)", placeholder="150.00")
            with a_cols[3]:
                tx_type = st.selectbox("Type", options=["expense", "income", "transfer"])
            with a_cols[4]:
                tx_cat = st.selectbox("Category (Optional for AI Suggestion)", options=["(Let AI Suggest)"] + sorted(list(ALLOWED_EXPENSE_CATEGORIES)))

            submitted = st.form_submit_button("Record Transaction", type="primary")
            if submitted:
                try:
                    paise = parse_amount_to_paise(tx_amount)
                    iso_date = tx_date.isoformat()
                    clean_desc = tx_desc.strip()
                    if not clean_desc:
                        st.error("Description cannot be empty.")
                    else:
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
                            if tx_cat == "(Let AI Suggest)":
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
                        st.success(f"Transaction recorded! Assigned category: {final_cat}")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

    # Query matching records
    matching_txs = db.get_transactions(
        year_month=st.session_state.selected_month,
        category=cat_filter if cat_filter != "All" else None,
        tx_type=type_filter if type_filter != "All" else None,
        search_query=st.session_state.search_query.strip() or None,
    )

    if matching_txs:
        st.write(f"Showing **{len(matching_txs)}** transactions.")
        # Tabular representation with inline category correction
        for tx in matching_txs:
            with st.container(border=True):
                r_cols = st.columns([1.2, 3.5, 1.5, 1.2, 2.2, 1.2])
                with r_cols[0]:
                    st.write(f"**{tx.date}**")
                    st.caption(tx.id)
                with r_cols[1]:
                    st.write(html.escape(tx.description))
                    badge = f'<span class="badge-review">Review ({tx.model_score:.2f})</span>' if tx.review_status == "needs_review" else '<span class="badge-confirmed">Confirmed</span>'
                    st.html(f'<span style="font-size:11px; color:#7A8499;">Source: {tx.category_source} • {badge}</span>')
                with r_cols[2]:
                    st.write(f"**{format_inr(tx.amount_paise)}**")
                with r_cols[3]:
                    st.write(f"`{tx.type}`")
                with r_cols[4]:
                    if tx.type == "expense":
                        cat_options = sorted(list(ALLOWED_EXPENSE_CATEGORIES))
                        cur_idx = cat_options.index(tx.category) if tx.category in cat_options else 0
                        new_cat = st.selectbox(
                            "Edit Cat",
                            options=cat_options,
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
                    if st.button("Delete", key=f"del_{tx.id}"):
                        db.delete_transaction(tx.id)
                        st.toast(f"Deleted {tx.id}")
                        st.rerun()
    else:
        st.info("No transactions match the selected criteria.")


# =============================================================================
# VIEW 3: BUDGETS
# =============================================================================
elif st.session_state.active_nav == "Budgets":
    st.subheader(f"Category Budgets — {datetime.strptime(st.session_state.selected_month, '%Y-%m').strftime('%B %Y')}")
    st.caption("Configure category targets and review deterministic spending rebalancing suggestions.")

    summary = calculate_monthly_summary(all_txs_for_month, st.session_state.selected_month)
    current_budgets = db.get_budgets(st.session_state.selected_month)
    comparisons = calculate_budget_comparisons(summary.expense_by_category_paise, current_budgets)

    b_left, b_right = st.columns([5, 5])

    with b_left:
        with st.container(border=True):
            st.write("#### Configure Monthly Budgets")
            st.caption("Amounts are in Indian Rupees (₹).")
            with st.form("set_budgets_form"):
                budget_inputs = {}
                for cat in sorted(list(ALLOWED_EXPENSE_CATEGORIES)):
                    cur_paise = current_budgets.get(cat, 0)
                    cur_inr = cur_paise / 100.0 if cur_paise else 0.0
                    budget_inputs[cat] = st.number_input(
                        f"{cat} Budget (₹)",
                        min_value=0.0,
                        value=float(cur_inr),
                        step=100.0,
                    )
                saved = st.form_submit_button("Save Budgets", type="primary")
                if saved:
                    for cat, val in budget_inputs.items():
                        paise_val = int(round(val * 100))
                        db.set_budget(st.session_state.selected_month, cat, paise_val)
                    st.success("Budgets updated successfully!")
                    st.rerun()

    with b_right:
        with st.container(border=True):
            st.write("#### Spending vs Target Analysis")
            for comp in comparisons:
                icon = "⚠️" if comp.is_over else "✅"
                st.write(f"**{icon} {comp.category}**")
                pct_str = f"{comp.percent_used:.1f}%" if comp.percent_used is not None else "N/A"
                b_str = format_inr(comp.budget_paise) if comp.budget_paise is not None else "Not set"
                st.write(f"• Spent: **{format_inr(comp.spent_paise)}** | Budget: **{b_str}** ({pct_str})")
                st.caption(f"Suggestion: {comp.suggestion}")
                st.divider()


# =============================================================================
# VIEW 4: CATEGORY REVIEW
# =============================================================================
elif st.session_state.active_nav == "Category Review":
    st.subheader("AI Category Review")
    st.caption("Review low-confidence or vocabulary-uncertain AI predictions and verify them.")

    pending_txs = db.get_transactions(review_status="needs_review")

    if not pending_txs:
        st.success("🎉 All transaction categories are confirmed! No items require review.")
    else:
        st.warning(f"**{len(pending_txs)}** transaction(s) require human review or confirmation.")

        for tx in pending_txs:
            with st.container(border=True):
                c_cols = st.columns([1.5, 4, 2, 2.5, 1.5])
                with c_cols[0]:
                    st.write(f"**{tx.date}**")
                    st.caption(tx.id)
                with c_cols[1]:
                    st.write(html.escape(tx.description))
                    score_str = f"Score: {tx.model_score:.2f}" if tx.model_score else "Score: N/A"
                    st.caption(f"Flagged by AI: {score_str} • Category: `{tx.category}`")
                with c_cols[2]:
                    st.write(f"**{format_inr(tx.amount_paise)}**")
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
                    if st.button("Confirm", key=f"btn_confirm_{tx.id}", type="primary"):
                        db.update_transaction_category(tx.id, chosen_cat, review_status="confirmed", category_source="manual")
                        st.toast(f"Confirmed {tx.id} as {chosen_cat}")
                        st.rerun()


# =============================================================================
# VIEW 5: MODEL EVALUATION
# =============================================================================
elif st.session_state.active_nav == "Model Evaluation":
    st.subheader("Machine Learning Model Evaluation & Transparency")
    st.caption("Honest reporting on offline TF-IDF + Logistic Regression performance against held-out data.")

    eval_json_path = Path("reports/model_evaluation.json")
    if eval_json_path.exists():
        with open(eval_json_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)

        meta = report_data.get("metadata", {})
        metrics = report_data.get("metrics", {})
        per_cat = report_data.get("per_category_metrics", {})

        e_cols = st.columns(4)
        with e_cols[0]:
            st.metric("Training Samples", meta.get("training_samples", 0))
        with e_cols[1]:
            st.metric("Holdout Samples", meta.get("holdout_samples", 0))
        with e_cols[2]:
            st.metric("Overall Accuracy", f"{metrics.get('overall_accuracy', 0.0) * 100:.1f}%")
        with e_cols[3]:
            st.metric("Abstention Rate", f"{metrics.get('abstention_rate', 0.0) * 100:.1f}%")

        st.write("")
        st.write("#### Per-Category Holdout Performance")
        per_cat_df = pd.DataFrame.from_dict(per_cat, orient="index")
        st.dataframe(per_cat_df, width="stretch")

        st.write("#### Methodological Disclosures & Limitations")
        for lim in report_data.get("honest_limitations", []):
            st.write(f"• {lim}")
    else:
        st.info("Evaluation report not found. Run `python scripts/evaluate_model.py` to generate it.")
