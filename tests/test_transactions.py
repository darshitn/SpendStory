"""Unit tests for transaction validation, paise math, and CSV parsing."""

import pytest

from src.transactions import (
    ALLOWED_EXPENSE_CATEGORIES,
    Transaction,
    compute_fingerprint,
    parse_amount_to_paise,
    parse_transactions_csv,
    validate_date,
    validate_transaction_row,
)


def test_parse_amount_to_paise_valid():
    assert parse_amount_to_paise("100") == 10000
    assert parse_amount_to_paise("100.00") == 10000
    assert parse_amount_to_paise("0.05") == 5
    assert parse_amount_to_paise("12.5") == 1250
    assert parse_amount_to_paise("9999.99") == 999999


def test_parse_amount_to_paise_invalid():
    # Negative
    with pytest.raises(ValueError, match="strictly positive"):
        parse_amount_to_paise("-10.00")
    # Zero
    with pytest.raises(ValueError, match="strictly positive"):
        parse_amount_to_paise("0")
    # Extra precision (> 2 decimals)
    with pytest.raises(ValueError, match="more than 2 decimal places"):
        parse_amount_to_paise("10.555")
    # Invalid strings
    with pytest.raises(ValueError, match="Invalid monetary amount"):
        parse_amount_to_paise("abc")
    with pytest.raises(ValueError, match="cannot be empty"):
        parse_amount_to_paise("")
    with pytest.raises(ValueError, match="cannot be empty"):
        parse_amount_to_paise(None)


def test_validate_date():
    assert validate_date("2026-10-15") == "2026-10-15"
    with pytest.raises(ValueError, match="strict YYYY-MM-DD"):
        validate_date("15-10-2026")
    with pytest.raises(ValueError, match="strict YYYY-MM-DD"):
        validate_date("2026/10/15")
    with pytest.raises(ValueError, match="Invalid calendar date"):
        validate_date("2026-02-31")


def test_validate_transaction_row_income_and_transfer():
    # Income normalizes category to Income
    row_inc = {
        "id": "TX-01",
        "date": "2026-10-01",
        "description": "Monthly stipend",
        "amount": "15000",
        "type": "income",
        "category": "",
    }
    tx_inc = validate_transaction_row(row_inc)
    assert tx_inc.type == "income"
    assert tx_inc.category == "Income"
    assert tx_inc.amount_paise == 1500000

    # Transfer normalizes category to Transfer
    row_tr = {
        "id": "TX-02",
        "date": "2026-10-02",
        "description": "ATM cash withdrawal",
        "amount": "2000.00",
        "type": "transfer",
        "category": "Random",
    }
    tx_tr = validate_transaction_row(row_tr)
    assert tx_tr.type == "transfer"
    assert tx_tr.category == "Transfer"
    assert tx_tr.amount_paise == 200000


def test_validate_transaction_row_expense():
    # Valid expense category
    row_exp = {
        "id": "TX-03",
        "date": "2026-10-03",
        "description": "Campus lunch",
        "amount": "250.50",
        "type": "expense",
        "category": "Food",
    }
    tx_exp = validate_transaction_row(row_exp)
    assert tx_exp.category == "Food"
    assert tx_exp.amount_paise == 25050
    assert tx_exp.review_status == "confirmed"

    # Empty category expense routes to needs_review
    row_uncat = {
        "id": "TX-04",
        "date": "2026-10-04",
        "description": "Unknown merchant",
        "amount": "100.00",
        "type": "expense",
        "category": "",
    }
    tx_uncat = validate_transaction_row(row_uncat)
    assert tx_uncat.category == ""
    assert tx_uncat.category_source == "model"
    assert tx_uncat.review_status == "needs_review"

    # Invalid expense category
    row_invalid_cat = {
        "id": "TX-05",
        "date": "2026-10-05",
        "description": "Crypto buy",
        "amount": "500",
        "type": "expense",
        "category": "Investment",
    }
    with pytest.raises(ValueError, match="Invalid expense category"):
        validate_transaction_row(row_invalid_cat)


def test_parse_transactions_csv_valid():
    csv_text = (
        "id,date,description,amount,type,category\n"
        "T1,2026-10-01,Allowance,10000.00,income,Income\n"
        "T2,2026-10-02,Lunch,150.00,expense,Food\n"
    )
    txs, errors = parse_transactions_csv(csv_text)
    assert len(errors) == 0
    assert len(txs) == 2
    assert txs[0].amount_paise == 1000000
    assert txs[1].amount_paise == 15000


def test_parse_transactions_csv_atomic_on_duplicate_id():
    csv_text = (
        "id,date,description,amount,type,category\n"
        "DUP-1,2026-10-01,Allowance,10000.00,income,Income\n"
        "DUP-1,2026-10-02,Lunch,150.00,expense,Food\n"
    )
    txs, errors = parse_transactions_csv(csv_text)
    assert len(txs) == 0  # Atomic rejection
    assert any("Duplicate ID 'DUP-1'" in e for e in errors)


def test_parse_transactions_csv_atomic_on_invalid_amount():
    csv_text = (
        "id,date,description,amount,type,category\n"
        "T1,2026-10-01,Allowance,10000.00,income,Income\n"
        "T2,2026-10-02,Lunch,-150.00,expense,Food\n"
    )
    txs, errors = parse_transactions_csv(csv_text)
    assert len(txs) == 0  # Atomic rejection
    assert any("strictly positive" in e for e in errors)


def test_parse_transactions_csv_invalid_header():
    csv_text = "wrong_id,date,description,amount,type,category\nT1,2026-10-01,Allowance,100,income,Income"
    txs, errors = parse_transactions_csv(csv_text)
    assert len(txs) == 0
    assert any("Invalid CSV header" in e for e in errors)


def test_compute_fingerprint():
    fp1 = compute_fingerprint("2026-10-01", "Canteen lunch", 15000, "expense")
    fp2 = compute_fingerprint("2026-10-01", "  canteen   lunch  ", 15000, "expense")
    fp3 = compute_fingerprint("2026-10-01", "Canteen lunch", 20000, "expense")
    assert fp1 == fp2
    assert fp1 != fp3
