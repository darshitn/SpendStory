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
    # Read EXPECTED_TOTALS.json
    expected_path = Path("data/demo/EXPECTED_TOTALS.json")
    with open(expected_path, "r", encoding="utf-8") as f:
        expected = json.load(f)

    # Read and parse demo transactions
    demo_csv = Path("data/demo/transactions.csv").read_bytes()
    transactions, errors = parse_transactions_csv(demo_csv)
    assert len(errors) == 0
    assert len(transactions) == 41

    # Verify October 2026
    oct_summary = calculate_monthly_summary(transactions, "2026-10")
    exp_oct = expected["2026-10"]

    assert oct_summary.row_count == exp_oct["rows"]
    assert oct_summary.income_paise == exp_oct["income_paise"]  # 1500000 paise (₹15,000)
    assert oct_summary.expense_paise == exp_oct["expense_paise"]  # 990000 paise (₹9,900)
    assert oct_summary.transfer_paise == exp_oct["transfer_paise"]  # 200000 paise (₹2,000)
    assert oct_summary.recorded_surplus_paise == exp_oct["recorded_surplus_paise"]  # 510000 paise (₹5,100)

    # Verify category-wise expense breakdown
    for cat, expected_paise in exp_oct["expense_by_category_paise"].items():
        assert oct_summary.expense_by_category_paise.get(cat, 0) == expected_paise

    # Verify November 2026
    nov_summary = calculate_monthly_summary(transactions, "2026-11")
    exp_nov = expected["2026-11"]

    assert nov_summary.row_count == exp_nov["rows"]
    assert nov_summary.income_paise == exp_nov["income_paise"]  # 1500000 paise (₹15,000)
    assert nov_summary.expense_paise == exp_nov["expense_paise"]  # 834000 paise (₹8,340)
    assert nov_summary.transfer_paise == exp_nov["transfer_paise"]  # 200000 paise (₹2,000)
    assert nov_summary.recorded_surplus_paise == exp_nov["recorded_surplus_paise"]  # 666000 paise (₹6,660)

    for cat, expected_paise in exp_nov["expense_by_category_paise"].items():
        assert nov_summary.expense_by_category_paise.get(cat, 0) == expected_paise


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
