"""Unit tests for financial calculations, aggregations, and safe export."""

import json
from pathlib import Path

from src.analytics import (
    calculate_budget_comparisons,
    calculate_cumulative_trend,
    calculate_monthly_summary,
    calculate_multi_month_comparison,
    export_transactions_to_csv,
    format_inr,
    sanitize_for_csv_cell,
)
from src.transactions import Transaction, parse_transactions_csv


def test_independent_demo_totals_verification():
    expected = json.loads(Path("data/demo/EXPECTED_TOTALS.json").read_text(encoding="utf-8"))
    transactions, errors = parse_transactions_csv(Path("data/demo/transactions.csv").read_bytes())
    assert not errors
    assert len(expected) == 12
    assert {tx.date[:7] for tx in transactions} == expected.keys()

    for month, totals in expected.items():
        summary = calculate_monthly_summary(transactions, month)
        assert summary.row_count == totals["rows"]
        assert summary.income_paise == totals["income_paise"]
        assert summary.expense_paise == totals["expense_paise"]
        assert summary.transfer_paise == totals["transfer_paise"]
        assert summary.recorded_surplus_paise == totals["recorded_surplus_paise"]
        assert summary.expense_by_category_paise == totals["expense_by_category_paise"]


def test_transfer_exclusion():
    txs = [
        Transaction(
            id="T1",
            date="2026-10-01",
            description="Allowance",
            amount_paise=1000000,
            type="income",
            category="Income",
        ),
        Transaction(
            id="T2",
            date="2026-10-02",
            description="Lunch",
            amount_paise=300000,
            type="expense",
            category="Food",
        ),
        Transaction(
            id="T3",
            date="2026-10-03",
            description="Bank transfer",
            amount_paise=500000,
            type="transfer",
            category="Transfer",
        ),
    ]

    summary = calculate_monthly_summary(txs, "2026-10")
    # Income = 1000000, Expense = 300000, Surplus = 700000, Transfer = 500000 (excluded from surplus)
    assert summary.income_paise == 1000000
    assert summary.expense_paise == 300000
    assert summary.recorded_surplus_paise == 700000
    assert summary.transfer_paise == 500000


def test_budget_comparisons_and_suggestions():
    spent = {"Food": 250000, "Transport": 80000}
    budgets = {"Food": 200000, "Transport": 100000}

    comps = calculate_budget_comparisons(spent, budgets)
    comp_map = {c.category: c for c in comps}

    # Food is over by ₹500 (50000 paise)
    food_comp = comp_map["Food"]
    assert food_comp.is_over is True
    assert food_comp.delta_paise == 50000
    assert "Reduce Food by ₹500.00" in food_comp.suggestion

    # Transport is under by ₹200
    tr_comp = comp_map["Transport"]
    assert tr_comp.is_over is False
    assert tr_comp.delta_paise == -20000
    assert "Under budget by ₹200.00" in tr_comp.suggestion


def test_format_inr():
    assert format_inr(1500000) == "₹15,000.00"
    assert format_inr(990000) == "₹9,900.00"
    assert format_inr(50) == "₹0.50"
    assert format_inr(-510000) == "-₹5,100.00"


def test_sanitize_and_safe_csv_export():
    assert sanitize_for_csv_cell("Normal text") == "Normal text"
    assert sanitize_for_csv_cell("=1+1") == "'=1+1"
    assert sanitize_for_csv_cell("+cmd") == "'+cmd"
    assert sanitize_for_csv_cell("-20") == "'-20"
    assert sanitize_for_csv_cell("@SUM(A1:A10)") == "'@SUM(A1:A10)"

    txs = [
        Transaction(
            id="T1",
            date="2026-10-01",
            description="=1+1 malicious formula",
            amount_paise=5000,
            type="expense",
            category="Food",
        )
    ]
    csv_str = export_transactions_to_csv(txs)
    assert "'=1+1 malicious formula" in csv_str


def test_budget_no_target_and_zero_target():
    spent = {"Food": 250000, "Books": 100000, "Shopping": 50000}
    budgets = {"Food": 200000, "Shopping": 0}  # Books has no target; Shopping has intentional zero target

    comps = calculate_budget_comparisons(spent, budgets)
    comp_map = {c.category: c for c in comps}

    # Books has no target set
    books_comp = comp_map["Books"]
    assert books_comp.budget_paise is None
    assert books_comp.is_over is False
    assert "No budget set for Books" in books_comp.suggestion

    # Shopping has intentional zero target and spent 50000 -> is_over
    shop_comp = comp_map["Shopping"]
    assert shop_comp.budget_paise == 0
    assert shop_comp.is_over is True
    assert shop_comp.delta_paise == 50000
    assert "Reduce Shopping by ₹500.00" in shop_comp.suggestion


def test_deficit_summary_and_trend_edge_cases():
    # Deficit: Expenses exceed income
    txs = [
        Transaction(id="T1", date="2026-10-05", description="Allowance", amount_paise=500000, type="income", category="Income"),
        Transaction(id="T2", date="2026-10-10", description="Fees", amount_paise=800000, type="expense", category="Education"),
    ]
    summary = calculate_monthly_summary(txs, "2026-10")
    assert summary.income_paise == 500000
    assert summary.expense_paise == 800000
    assert summary.recorded_surplus_paise == -300000  # -₹3,000 deficit

    # Trend with single transaction
    trend_single = calculate_cumulative_trend([txs[0]], "2026-10")
    assert len(trend_single) == 1
    assert trend_single[0]["date"] == "2026-10-05"
    assert trend_single[0]["income_inr"] == 5000.0

    # Trend with zero transactions
    trend_empty = calculate_cumulative_trend([], "2026-10")
    assert trend_empty == []
