"""Student Finance Assistant — Personal Money Management Dashboard.

Visual design adheres strictly to the Dribbble 'Nexora' Money Management Dashboard
(ILmix Studio / Atiqur Rahman) visual brief in handoff/DRIBBBLE_UI_PROMPT.md.
"""

from __future__ import annotations

from datetime import date, datetime
import html
import json
from pathlib import Path
from typing import Optional

import altair as alt
import pandas as pd
import streamlit as st

from src.analytics import (
    BudgetComparison,
    calculate_budget_comparisons,
    calculate_cumulative_trend,
    calculate_monthly_summary,
    calculate_multi_month_comparison,
    export_transactions_to_csv,
    format_inr,
)
from src.categorizer import DEFAULT_CONFIDENCE_THRESHOLD, get_default_categorizer
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
    page_title="Nexora — Student Finance Assistant",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Scoped CSS matching the Dribbble Nexora visual design brief:
# Pale lavender background, rounded white application shell, subtle borders,
# modern sans typography, compact top toolbar, and quiet sidebar.
NEXORA_CSS = """
<style>
/* Root styling and Pale Lavender backdrop */
.stApp {
    background-color: #E2E7F5 !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    color: #14182D;
}

/* Rounded white application shell */
.main .block-container {
    max-width: 1400px !important;
    padding: 24px 32px 40px 32px !important;
    background-color: #FFFFFF !important;
    border-radius: 28px !important;
    box-shadow: 0 16px 48px -12px rgba(20, 24, 45, 0.08) !important;
    border: 1px solid rgba(178, 188, 226, 0.45) !important;
    margin-top: 16px !important;
    margin-bottom: 24px !important;
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

/* Nexora Wordmark branding */
.nexora-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 22px;
    font-weight: 800;
    color: #14182D;
    letter-spacing: -0.5px;
    margin-bottom: 24px;
    padding-left: 6px;
}

.nexora-logo-icon {
    width: 28px;
    height: 28px;
    background: linear-gradient(135deg, #373EDC 0%, #993FC5 100%);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 14px;
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
.top-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 16px;
    margin-bottom: 8px;
    border-bottom: 1px solid #F1F4FA;
}

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
    color: #7A8499;
    text-transform: capitalize;
    letter-spacing: 0.2px;
}

.metric-figure {
    font-size: 26px;
    font-weight: 700;
    color: #14182D;
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

/* Visualization Panel Cards */
.panel-card {
    background-color: #FFFFFF;
    border: 1px solid #EAEFF7;
    border-radius: 18px;
    padding: 22px 24px;
    height: 100%;
    box-shadow: 0 4px 16px rgba(20, 24, 45, 0.02);
}

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

.panel-action {
    color: #8E95A9;
    font-size: 12px;
    cursor: pointer;
}

/* Category Budget Row */
.budget-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
}

.budget-cat-name {
    font-size: 13px;
    font-weight: 600;
    color: #14182D;
}

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
</style>
"""
st.html(NEXORA_CSS)


# -----------------------------------------------------------------------------
# Database & State Initialization
# -----------------------------------------------------------------------------
@st.cache_resource
def get_database() -> Database:
    return Database("storage/finance.db")


db = get_database()
categorizer = get_default_categorizer()

# Initialize session state variables
if "active_nav" not in st.session_state:
    st.session_state.active_nav = "Overview"

if "search_query" not in st.session_state:
    st.session_state.search_query = ""

if "confirm_reset" not in st.session_state:
    st.session_state.confirm_reset = False

if "selected_month" not in st.session_state:
    available_months = db.get_available_months()
    st.session_state.selected_month = available_months[0] if available_months else "2026-10"


# -----------------------------------------------------------------------------
# Sidebar Navigation & Actions
# -----------------------------------------------------------------------------
with st.sidebar:
    # Nexora Wordmark
    st.html(
        """
        <div class="nexora-logo">
            <div class="nexora-logo-icon">✦</div>
            <span>Nexora</span>
        </div>
        """
    )

    # Count items needing review for navigation badge
    unreviewed_items = db.get_transactions(review_status="needs_review")
    review_label = f"Category Review ({len(unreviewed_items)})" if unreviewed_items else "Category Review"

    nav_options = [
        "Overview",
        "Transactions",
        "Budgets",
        review_label,
        "Model Evaluation",
    ]

    selected_nav = st.radio(
        "Navigation",
        options=nav_options,
        index=0 if st.session_state.active_nav == "Overview" else (
            1 if st.session_state.active_nav == "Transactions" else (
                2 if st.session_state.active_nav == "Budgets" else (
                    3 if "Category Review" in st.session_state.active_nav else 4
                )
            )
        ),
        label_visibility="collapsed",
    )

    # Normalize active nav name
    if "Category Review" in selected_nav:
        st.session_state.active_nav = "Category Review"
    else:
        st.session_state.active_nav = selected_nav

    st.divider()

    # Sidebar Action Card (Replacing 'Upgrade to Pro' with Fictional Demo loader)
    st.html(
        """
        <div class="sidebar-promo-card">
            <div class="sidebar-promo-title">Fictional Demo</div>
            <div class="sidebar-promo-desc">
                Load verified student dataset with Oct & Nov 2026 totals and budget baselines.
            </div>
        </div>
        """
    )

    if st.button("Load Fictional Demo", type="primary", width="stretch"):
        res = db.load_demo_data("data/demo/transactions.csv")
        st.session_state.selected_month = "2026-10"
        st.toast(f"Demo loaded! Inserted: {res.inserted}, Skipped: {res.skipped}")
        st.rerun()

    st.write("")
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
available_months = db.get_available_months()
if not available_months:
    available_months = ["2026-10", "2026-11"]

if st.session_state.selected_month not in available_months:
    st.session_state.selected_month = available_months[0]

toolbar_cols = st.columns([3, 2, 2, 1.2, 1.2])

with toolbar_cols[0]:
    st.html(f'<h1 class="view-title">{st.session_state.active_nav}</h1>')

with toolbar_cols[1]:
    search_input = st.text_input(
        "Search",
        value=st.session_state.search_query,
        placeholder="🔍 Search transactions...",
        label_visibility="collapsed",
    )
    if search_input != st.session_state.search_query:
        st.session_state.search_query = search_input
        if search_input and st.session_state.active_nav == "Overview":
            st.session_state.active_nav = "Transactions"
        st.rerun()

with toolbar_cols[2]:
    selected_month_choice = st.selectbox(
        "Month",
        options=available_months,
        index=available_months.index(st.session_state.selected_month) if st.session_state.selected_month in available_months else 0,
        format_func=lambda ym: datetime.strptime(ym, "%Y-%m").strftime("%B %Y") if ym else ym,
        label_visibility="collapsed",
    )
    if selected_month_choice != st.session_state.selected_month:
        st.session_state.selected_month = selected_month_choice
        st.rerun()

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
    # Greeting Row
    month_name = datetime.strptime(st.session_state.selected_month, "%Y-%m").strftime("%B %Y")
    st.html(
        f"""
        <div class="greeting-header">Good Day, Student 👋</div>
        <div class="greeting-subtext">Viewing financial summary and budget tracking for {month_name} • Fictional Demo Data</div>
        """
    )

    # 1. Four Equal Summary Cards
    summary = calculate_monthly_summary(all_txs_for_month, st.session_state.selected_month)
    surplus_class = "green" if summary.recorded_surplus_paise >= 0 else "purple"

    metric_cols = st.columns(4)

    with metric_cols[0]:
        st.html(
            f"""
            <div class="metric-card">
                <div class="metric-top-row">
                    <span class="metric-label">Recorded Income</span>
                    <span style="color:#A0AEC0; font-size:14px;">⋮</span>
                </div>
                <div class="metric-figure">{format_inr(summary.income_paise)}</div>
                <div class="metric-badge green">↗ Active month allowance</div>
            </div>
            """
        )

    with metric_cols[1]:
        st.html(
            f"""
            <div class="metric-card">
                <div class="metric-top-row">
                    <span class="metric-label">Recorded Expenses</span>
                    <span style="color:#A0AEC0; font-size:14px;">⋮</span>
                </div>
                <div class="metric-figure">{format_inr(summary.expense_paise)}</div>
                <div class="metric-badge purple">↘ Total outflow</div>
            </div>
            """
        )

    with metric_cols[2]:
        st.html(
            f"""
            <div class="metric-card">
                <div class="metric-top-row">
                    <span class="metric-label">Recorded Surplus</span>
                    <span style="color:#A0AEC0; font-size:14px;">⋮</span>
                </div>
                <div class="metric-figure">{format_inr(summary.recorded_surplus_paise)}</div>
                <div class="metric-badge {surplus_class}">Income minus expenses</div>
            </div>
            """
        )

    with metric_cols[3]:
        st.html(
            f"""
            <div class="metric-card">
                <div class="metric-top-row">
                    <span class="metric-label">Transfers Excluded</span>
                    <span style="color:#A0AEC0; font-size:14px;">⋮</span>
                </div>
                <div class="metric-figure">{format_inr(summary.transfer_paise)}</div>
                <div class="metric-badge blue">Internal account moves</div>
            </div>
            """
        )

    st.write("")

    # 2. Main Visualization Row (70% Trend Chart / 30% Category Doughnut)
    row1_left, row1_right = st.columns([6.8, 3.2])

    with row1_left:
        with st.container(border=True):
            st.html(
                f"""
                <div class="panel-header">
                    <div>
                        <div class="panel-title">Cumulative Income & Expense Trend</div>
                        <div style="font-size:22px; font-weight:700; color:#14182D; margin-top:4px;">
                            {format_inr(summary.recorded_surplus_paise)}
                            <span style="font-size:12px; font-weight:500; color:#0E9F6E; margin-left:6px;">Surplus</span>
                        </div>
                    </div>
                    <span style="font-size:12px; color:#8E95A9;">Truthful dated timeline</span>
                </div>
                """
            )

            trend_data = calculate_cumulative_trend(all_txs_for_month, st.session_state.selected_month)
            if trend_data:
                # Prepare melted dataframe for dual area Altair chart
                df_trend = pd.DataFrame(trend_data)
                df_melted = df_trend.melt(
                    id_vars=["date", "label"],
                    value_vars=["income_inr", "expense_inr"],
                    var_name="Series",
                    value_name="Amount",
                )
                df_melted["SeriesName"] = df_melted["Series"].map(
                    {"income_inr": "Cumulative Income", "expense_inr": "Cumulative Expenses"}
                )

                # Altair custom chart with soft violet / indigo aesthetic
                base = alt.Chart(df_melted).encode(
                    x=alt.X("label:N", title=None, axis=alt.Axis(labelAngle=0, labelColor="#7A8499", gridColor="#F1F4FA")),
                    y=alt.Y("Amount:Q", title="Amount (₹)", axis=alt.Axis(format="~s", labelColor="#7A8499", gridColor="#F1F4FA")),
                    color=alt.Color(
                        "SeriesName:N",
                        scale=alt.Scale(domain=["Cumulative Income", "Cumulative Expenses"], range=["#373EDC", "#C026D3"]),
                        legend=alt.Legend(orient="top", title=None, labelColor="#4A5568"),
                    ),
                )

                # Line with subtle point marks and area translucency
                area = base.mark_area(opacity=0.12, interpolate="monotone")
                line = base.mark_line(strokeWidth=2.8, interpolate="monotone")
                points = base.mark_circle(size=40, opacity=0.8)

                chart_trend = (area + line + points).properties(height=260).interactive()
                st.altair_chart(chart_trend, width="stretch")
            else:
                st.info("No recorded transactions found for this month.")

    with row1_right:
        with st.container(border=True):
            st.html(
                """
                <div class="panel-header">
                    <span class="panel-title">Monthly Expenses Breakdown</span>
                    <span style="color:#A0AEC0; font-size:14px;">⋮</span>
                </div>
                """
            )

            if summary.expense_by_category_paise and summary.expense_paise > 0:
                donut_rows = []
                for cat, paise in summary.expense_by_category_paise.items():
                    pct = round((paise / summary.expense_paise) * 100, 1)
                    donut_rows.append({"Category": cat, "Amount": paise / 100.0, "Share": pct})

                df_donut = pd.DataFrame(donut_rows)

                # Dribbble violet/indigo/magenta color palette
                palette = ["#993FC5", "#373EDC", "#B3B3F4", "#C7A7F0", "#38BDF8", "#F43F5E", "#10B981"]
                donut_chart = (
                    alt.Chart(df_donut)
                    .mark_arc(innerRadius=62, outerRadius=95, stroke="#FFFFFF", strokeWidth=2)
                    .encode(
                        theta=alt.Theta("Amount:Q", title="Amount"),
                        color=alt.Color("Category:N", scale=alt.Scale(range=palette), legend=None),
                        tooltip=[
                            alt.Tooltip("Category:N"),
                            alt.Tooltip("Amount:Q", format=",.2f", title="Spent (₹)"),
                            alt.Tooltip("Share:Q", format=".1f", title="Share (%)"),
                        ],
                    )
                    .properties(height=200)
                )

                # Center text showing total expense
                center_text = (
                    alt.Chart(pd.DataFrame([{"text": format_inr(summary.expense_paise)}]))
                    .mark_text(fontSize=16, fontWeight=700, color="#14182D")
                    .encode(text="text:N")
                )

                st.altair_chart(donut_chart + center_text, width="stretch")

                # Compact category legend
                legend_cols = st.columns(2)
                for idx, row in df_donut.iterrows():
                    col_idx = idx % 2
                    color = palette[idx % len(palette)]
                    with legend_cols[col_idx]:
                        st.html(
                            f"""
                            <div style="display:flex; align-items:center; gap:6px; font-size:11.5px; margin-bottom:4px;">
                                <span style="width:8px; height:8px; border-radius:50%; background-color:{color};"></span>
                                <span style="color:#4A5568; font-weight:500;">{row['Category']}</span>
                                <span style="color:#7A8499; margin-left:auto;">{row['Share']:.0f}%</span>
                            </div>
                            """
                        )
            else:
                st.caption("No recorded expenses for this period.")

    st.write("")

    # 3. Lower Visualization Row (30% Monthly Budgets / 70% Monthly Comparison)
    row2_left, row2_right = st.columns([3.5, 6.5])

    with row2_left:
        with st.container(border=True):
            st.html(
                """
                <div class="panel-header">
                    <span class="panel-title">Monthly Budgets</span>
                    <span style="color:#A0AEC0; font-size:14px;">⋮</span>
                </div>
                """
            )

            budgets_map = db.get_budgets(st.session_state.selected_month)
            comparisons = calculate_budget_comparisons(summary.expense_by_category_paise, budgets_map)

            # Category icons
            cat_icons = {
                "Food": "🍽️",
                "Transport": "🚌",
                "Shopping": "🛍️",
                "Education": "🎓",
                "Bills": "⚡",
                "Entertainment": "🎬",
                "Other": "📦",
            }
            track_colors = ["#10B981", "#373EDC", "#993FC5", "#F59E0B", "#38BDF8", "#EC4899", "#8B5CF6"]

            if comparisons:
                for idx, comp in enumerate(comparisons[:5]):
                    icon = cat_icons.get(comp.category, "🏷️")
                    color = track_colors[idx % len(track_colors)]
                    pct = comp.percent_used if comp.percent_used is not None else 0.0
                    capped_pct = min(pct, 100.0)

                    status_html = ""
                    if comp.budget_paise is None:
                        status_html = '<span style="font-size:11px; color:#A0AEC0;">No budget set</span>'
                    elif comp.is_over:
                        status_html = f'<span style="font-size:11px; font-weight:700; color:#E02424;">+{format_inr(comp.delta_paise)} Over</span>'
                    else:
                        status_html = f'<span style="font-size:11px; font-weight:600; color:#0E9F6E;">{pct:.0f}%</span>'

                    st.html(
                        f"""
                        <div style="margin-bottom:12px;">
                            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:2px;">
                                <div style="display:flex; align-items:center; gap:8px;">
                                    <span style="font-size:14px;">{icon}</span>
                                    <span style="font-size:13px; font-weight:600; color:#14182D;">{comp.category}</span>
                                </div>
                                <div style="text-align:right;">
                                    <span style="font-size:12px; font-weight:600; color:#14182D;">{format_inr(comp.spent_paise)}</span>
                                    {f'<span style="font-size:11px; color:#8E95A9;"> / {format_inr(comp.budget_paise)}</span>' if comp.budget_paise else ''}
                                </div>
                            </div>
                            <div class="budget-progress-track">
                                <div class="budget-progress-fill" style="width:{capped_pct}%; background-color:{color};"></div>
                            </div>
                            <div style="margin-top:2px; display:flex; justify-content:space-between;">
                                <span style="font-size:10.5px; color:#8E95A9;">{comp.suggestion or ''}</span>
                                {status_html}
                            </div>
                        </div>
                        """
                    )
            else:
                st.caption("No budget data available.")

    with row2_right:
        with st.container(border=True):
            st.html(
                """
                <div class="panel-header">
                    <div>
                        <div class="panel-title">Monthly Income vs Expenses Comparison</div>
                        <div style="font-size:12px; color:#8E95A9; margin-top:2px;">
                            Solid indigo bars: Income (positive) • Striped/lavender bars: Expense magnitude (spending outflow)
                        </div>
                    </div>
                    <span style="color:#A0AEC0; font-size:14px;">⋮</span>
                </div>
                """
            )

            all_txs_dataset = db.get_transactions()
            multi_month = calculate_multi_month_comparison(all_txs_dataset)

            if multi_month:
                comp_rows = []
                for mm in multi_month:
                    # Income above baseline (+ve)
                    comp_rows.append(
                        {
                            "Month": mm["month_label"],
                            "Type": "Income",
                            "Amount": mm["income_inr"],
                            "DisplayAmount": f"₹{mm['income_inr']:,.2f}",
                        }
                    )
                    # Expense below baseline (-ve for mirrored layout, with positive tooltip magnitude)
                    comp_rows.append(
                        {
                            "Month": mm["month_label"],
                            "Type": "Expenses",
                            "Amount": -mm["expense_inr"],
                            "DisplayAmount": f"₹{mm['expense_inr']:,.2f}",
                        }
                    )

                df_mm = pd.DataFrame(comp_rows)

                mirrored_bar = (
                    alt.Chart(df_mm)
                    .mark_bar(cornerRadius=6, size=28)
                    .encode(
                        x=alt.X("Month:N", title=None, axis=alt.Axis(labelAngle=0, labelColor="#4A5568")),
                        y=alt.Y(
                            "Amount:Q",
                            title="Net Flow (₹)",
                            axis=alt.Axis(
                                format="~s",
                                labelColor="#7A8499",
                                gridColor="#F1F4FA",
                            ),
                        ),
                        color=alt.Color(
                            "Type:N",
                            scale=alt.Scale(domain=["Income", "Expenses"], range=["#373EDC", "#B3B3F4"]),
                            legend=alt.Legend(orient="top", title=None),
                        ),
                        tooltip=[
                            alt.Tooltip("Month:N"),
                            alt.Tooltip("Type:N"),
                            alt.Tooltip("DisplayAmount:N", title="Recorded Amount"),
                        ],
                    )
                    .properties(height=260)
                )

                rule = alt.Chart(pd.DataFrame([{"y": 0}])).mark_rule(color="#CBD5E1", strokeWidth=1).encode(y="y:Q")

                st.altair_chart(mirrored_bar + rule, width="stretch")
            else:
                st.caption("No multi-month records available.")


# =============================================================================
# VIEW 2: TRANSACTIONS
# =============================================================================
elif st.session_state.active_nav == "Transactions":
    st.subheader(f"Transactions — {datetime.strptime(st.session_state.selected_month, '%Y-%m').strftime('%B %Y')}")
    st.caption("Browse, search, edit categories, and record student financial entries.")

    # Top Filters & Add Transaction Expander
    f_cols = st.columns([3, 2, 2, 2])
    with f_cols[0]:
        t_search = st.text_input("Filter by description", value=st.session_state.search_query, placeholder="Filter by text...")
    with f_cols[1]:
        type_filter = st.selectbox("Type", options=["All", "income", "expense", "transfer"])
    with f_cols[2]:
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
        search_query=t_search if t_search else None,
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
