"""Financial calculations, budgeting arithmetic, aggregations, and safe CSV export.

All core sums and balances are computed in integer paise.
Transfers are strictly excluded from income, expense, and surplus calculations.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
import io
from typing import Optional

from src.transactions import Transaction


@dataclass(frozen=True)
class MonthlySummary:
    year_month: str
    income_paise: int
    expense_paise: int
    recorded_surplus_paise: int
    transfer_paise: int
    expense_by_category_paise: dict[str, int]
    row_count: int

    @property
    def income_inr(self) -> float:
        return self.income_paise / 100.0

    @property
    def expense_inr(self) -> float:
        return self.expense_paise / 100.0

    @property
    def recorded_surplus_inr(self) -> float:
        return self.recorded_surplus_paise / 100.0

    @property
    def transfer_inr(self) -> float:
        return self.transfer_paise / 100.0


@dataclass(frozen=True)
class BudgetComparison:
    category: str
    spent_paise: int
    budget_paise: Optional[int]
    is_over: bool
    delta_paise: int  # positive means overspent, negative means underspent
    percent_used: Optional[float]
    suggestion: Optional[str]

    @property
    def spent_inr(self) -> float:
        return self.spent_paise / 100.0

    @property
    def budget_inr(self) -> Optional[float]:
        return self.budget_paise / 100.0 if self.budget_paise is not None else None

    @property
    def delta_inr(self) -> float:
        return abs(self.delta_paise) / 100.0


def format_inr(amount_paise: int, show_sign: bool = False) -> str:
    """Format paise as a standard Indian Rupee string (e.g. '₹15,000.00')."""
    is_negative = amount_paise < 0
    abs_paise = abs(amount_paise)
    rupees = abs_paise // 100
    paise = abs_paise % 100

    s = str(rupees)
    if len(s) > 3:
        last3 = s[-3:]
        rest = s[:-3]
        groups = []
        while len(rest) > 2:
            groups.append(rest[-2:])
            rest = rest[:-2]
        if rest:
            groups.append(rest)
        groups.reverse()
        formatted_rupees = ",".join(groups) + "," + last3
    else:
        formatted_rupees = s

    formatted = f"₹{formatted_rupees}.{paise:02d}"
    if is_negative:
        return f"-{formatted}"
    if show_sign and amount_paise > 0:
        return f"+{formatted}"
    return formatted


def calculate_monthly_summary(transactions: list[Transaction], year_month: str) -> MonthlySummary:
    """Compute financial summary for a given month in integer paise."""
    month_txs = [tx for tx in transactions if tx.date.startswith(year_month)]

    income_paise = 0
    expense_paise = 0
    transfer_paise = 0
    expense_by_category: dict[str, int] = {}

    for tx in month_txs:
        if tx.type == "income":
            income_paise += tx.amount_paise
        elif tx.type == "expense":
            expense_paise += tx.amount_paise
            cat = tx.category or "Other"
            expense_by_category[cat] = expense_by_category.get(cat, 0) + tx.amount_paise
        elif tx.type == "transfer":
            transfer_paise += tx.amount_paise

    surplus_paise = income_paise - expense_paise

    return MonthlySummary(
        year_month=year_month,
        income_paise=income_paise,
        expense_paise=expense_paise,
        recorded_surplus_paise=surplus_paise,
        transfer_paise=transfer_paise,
        expense_by_category_paise=expense_by_category,
        row_count=len(month_txs),
    )


def calculate_budget_comparisons(
    expense_by_category_paise: dict[str, int],
    budgets_paise: dict[str, int],
) -> list[BudgetComparison]:
    """Compare category expenses against user targets and generate deterministic suggestions."""
    all_categories = sorted(set(list(expense_by_category_paise.keys()) + list(budgets_paise.keys())))
    comparisons: list[BudgetComparison] = []

    for cat in all_categories:
        spent = expense_by_category_paise.get(cat, 0)
        budget = budgets_paise.get(cat)

        if budget is None:
            comparisons.append(
                BudgetComparison(
                    category=cat,
                    spent_paise=spent,
                    budget_paise=None,
                    is_over=False,
                    delta_paise=0,
                    percent_used=None,
                    suggestion=f"No budget set for {cat}. Set target to track progress.",
                )
            )
        else:
            delta = spent - budget
            is_over = delta > 0
            percent_used = round((spent / budget) * 100.0, 1) if budget > 0 else (100.0 if spent > 0 else 0.0)

            if is_over:
                delta_str = format_inr(delta)
                target_str = format_inr(budget)
                suggestion = f"Reduce {cat} by {delta_str} to meet target budget of {target_str}."
            else:
                remaining_str = format_inr(budget - spent)
                suggestion = f"Under budget by {remaining_str}."

            comparisons.append(
                BudgetComparison(
                    category=cat,
                    spent_paise=spent,
                    budget_paise=budget,
                    is_over=is_over,
                    delta_paise=delta,
                    percent_used=percent_used,
                    suggestion=suggestion,
                )
            )

    return comparisons


def calculate_cumulative_trend(transactions: list[Transaction], year_month: str) -> list[dict]:
    """Calculate truthful cumulative income and expense across days of the selected month.

    Derived exclusively from dated records (linear progression, no fabricated curves).
    """
    month_txs = [tx for tx in transactions if tx.date.startswith(year_month)]
    if not month_txs:
        return []

    # Sort transactions by date ascending
    sorted_txs = sorted(month_txs, key=lambda tx: (tx.date, tx.id))

    # Aggregate daily changes
    daily_income: dict[str, int] = {}
    daily_expense: dict[str, int] = {}

    dates = sorted({tx.date for tx in sorted_txs})

    for tx in sorted_txs:
        if tx.type == "income":
            daily_income[tx.date] = daily_income.get(tx.date, 0) + tx.amount_paise
        elif tx.type == "expense":
            daily_expense[tx.date] = daily_expense.get(tx.date, 0) + tx.amount_paise

    # Cumulative running sums
    running_inc = 0
    running_exp = 0
    records = []

    for d in dates:
        running_inc += daily_income.get(d, 0)
        running_exp += daily_expense.get(d, 0)
        formatted_day = datetime.strptime(d, "%Y-%m-%d").strftime("%b %d")
        records.append(
            {
                "date": d,
                "label": formatted_day,
                "income_paise": running_inc,
                "income_inr": running_inc / 100.0,
                "expense_paise": running_exp,
                "expense_inr": running_exp / 100.0,
            }
        )

    return records


def calculate_multi_month_comparison(transactions: list[Transaction]) -> list[dict]:
    """Calculate monthly income and expense totals for actual recorded months.

    Expenses are returned as positive spending magnitudes for display.
    """
    months = sorted({tx.date[:7] for tx in transactions if tx.date})
    results = []

    for ym in months:
        summary = calculate_monthly_summary(transactions, ym)
        month_label = datetime.strptime(ym, "%Y-%m").strftime("%b %Y")
        results.append(
            {
                "year_month": ym,
                "month_label": month_label,
                "income_paise": summary.income_paise,
                "income_inr": summary.income_inr,
                "expense_paise": summary.expense_paise,
                "expense_inr": summary.expense_inr,
                "recorded_surplus_inr": summary.recorded_surplus_inr,
            }
        )

    return results


def sanitize_for_csv_cell(value: str) -> str:
    """Protect against spreadsheet formula injection.

    If cell starts with =, +, -, @, tab, or carriage return, prepend a single quote.
    """
    s = str(value)
    if s and s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{s}"
    return s


def export_transactions_to_csv(transactions: list[Transaction]) -> str:
    """Generate RFC 4180 CSV string with formula injection protection."""
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\r\n")

    writer.writerow(["id", "date", "description", "amount", "type", "category"])

    for tx in transactions:
        writer.writerow(
            [
                sanitize_for_csv_cell(tx.id),
                sanitize_for_csv_cell(tx.date),
                sanitize_for_csv_cell(tx.description),
                f"{tx.amount_paise / 100.0:.2f}",
                sanitize_for_csv_cell(tx.type),
                sanitize_for_csv_cell(tx.category),
            ]
        )

    return output.getvalue()
