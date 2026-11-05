"""Unit tests for SQLite storage, idempotent imports, and persistence."""

import pytest

from src.storage import Database, ImportResult
from src.transactions import Transaction, compute_fingerprint


@pytest.fixture
def db():
    # Use in-memory SQLite database for isolated test execution
    return Database(":memory:")


def make_sample_tx(
    tx_id="T1",
    date="2026-10-01",
    desc="Lunch",
    amount_paise=15000,
    tx_type="expense",
    category="Food",
):
    fp = compute_fingerprint(date, desc, amount_paise, tx_type)
    return Transaction(
        id=tx_id,
        date=date,
        description=desc,
        amount_paise=amount_paise,
        type=tx_type,
        category=category,
        fingerprint=fp,
    )


def test_add_and_get_transaction(db):
    tx = make_sample_tx("T1", "2026-10-01", "College canteen lunch", 15000, "expense", "Food")
    db.add_transaction(tx)

    fetched = db.get_transaction("T1")
    assert fetched is not None
    assert fetched.id == "T1"
    assert fetched.amount_paise == 15000
    assert fetched.category == "Food"

    # Duplicate ID insert should raise
    with pytest.raises(ValueError, match="already exists"):
        db.add_transaction(tx)


def test_idempotent_import_skips_identical_payload(db):
    tx1 = make_sample_tx("T1", "2026-10-01", "Lunch", 15000, "expense", "Food")
    res1 = db.save_transactions([tx1])
    assert res1.inserted == 1
    assert res1.skipped == 0
    assert len(res1.conflicts) == 0

    # User modifies category manually
    db.update_transaction_category("T1", "Other", review_status="confirmed")
    updated = db.get_transaction("T1")
    assert updated.category == "Other"

    # Re-import identical original payload
    res2 = db.save_transactions([tx1])
    assert res2.inserted == 0
    assert res2.skipped == 1
    assert len(res2.conflicts) == 0

    # Verify user's manual category update was preserved!
    preserved = db.get_transaction("T1")
    assert preserved.category == "Other"


def test_import_detects_conflicting_id_payload(db):
    tx1 = make_sample_tx("T1", "2026-10-01", "Lunch", 15000, "expense", "Food")
    db.save_transactions([tx1])

    # Different transaction reusing ID 'T1'
    tx1_conflict = make_sample_tx("T1", "2026-10-02", "Different Description", 50000, "expense", "Shopping")
    res = db.save_transactions([tx1_conflict])

    assert res.inserted == 0
    assert res.skipped == 0
    assert len(res.conflicts) == 1
    assert "already exists with different details" in res.conflicts[0]

    # Original data untouched
    orig = db.get_transaction("T1")
    assert orig.amount_paise == 15000


def test_budget_persistence(db):
    db.set_budget("2026-10", "Food", 300000)
    db.set_budget("2026-10", "Transport", 100000)

    budgets = db.get_budgets("2026-10")
    assert budgets["Food"] == 300000
    assert budgets["Transport"] == 100000

    # Update budget
    db.set_budget("2026-10", "Food", 350000)
    budgets_updated = db.get_budgets("2026-10")
    assert budgets_updated["Food"] == 350000

    # Delete budget (sets to No target)
    deleted = db.delete_budget("2026-10", "Food")
    assert deleted is True
    budgets_after_del = db.get_budgets("2026-10")
    assert "Food" not in budgets_after_del
    assert budgets_after_del["Transport"] == 100000


def test_load_demo_data_idempotency(db):
    res1 = db.load_demo_data("data/demo/transactions.csv")
    assert res1.inserted == 41
    assert res1.skipped == 0
    assert len(res1.conflicts) == 0

    # Repeat load must not duplicate rows
    res2 = db.load_demo_data("data/demo/transactions.csv")
    assert res2.inserted == 0
    assert res2.skipped == 41
    assert len(res2.conflicts) == 0

    months = db.get_available_months()
    assert "2026-10" in months
    assert "2026-11" in months
