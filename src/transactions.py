"""Transaction data structures, validation, and CSV parsing.

All monetary values are converted to and represented as integer paise (1 INR = 100 paise).
Binary floating-point arithmetic is never used for financial calculations.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
import hashlib
import io
import re
from typing import Optional

ALLOWED_EXPENSE_CATEGORIES = {
    "Food",
    "Transport",
    "Shopping",
    "Education",
    "Bills",
    "Entertainment",
    "Other",
}

VALID_TYPES = {"income", "expense", "transfer"}
EXPECTED_HEADERS = ["id", "date", "description", "amount", "type", "category"]
MAX_CSV_BYTES = 2 * 1024 * 1024  # 2 MB
MAX_CSV_ROWS = 10000


@dataclass(frozen=True)
class Transaction:
    id: str
    date: str  # YYYY-MM-DD
    description: str
    amount_paise: int
    type: str  # 'income', 'expense', 'transfer'
    category: str
    category_source: str = "imported"  # 'imported', 'manual', 'model'
    review_status: str = "confirmed"  # 'confirmed', 'needs_review'
    model_score: Optional[float] = None
    fingerprint: str = ""

    @property
    def amount_inr(self) -> float:
        """Helper to return INR float strictly for UI display purposes."""
        return self.amount_paise / 100.0


def compute_fingerprint(date_str: str, description: str, amount_paise: int, tx_type: str) -> str:
    """Compute a SHA-256 hash of the transaction's core payload.

    Used to detect re-imported identical transactions vs conflicting ID modifications.
    """
    normalized_desc = " ".join(description.strip().split()).lower()
    raw = f"{date_str.strip()}|{normalized_desc}|{amount_paise}|{tx_type.strip().lower()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def parse_amount_to_paise(val: str | int | float | Decimal) -> int:
    """Parse and validate an amount string or number to integer paise.

    Rules:
    - Must be positive (> 0)
    - Must have at most 2 decimal places
    - Must not be NaN, Infinity, negative, or zero
    """
    if val is None:
        raise ValueError("Amount cannot be empty.")

    s = str(val).strip()
    if not s:
        raise ValueError("Amount cannot be empty.")

    try:
        d = Decimal(s)
    except InvalidOperation as e:
        raise ValueError(f"Invalid monetary amount: '{s}'") from e

    if not d.is_finite():
        raise ValueError("Amount must be a finite number.")

    if d <= 0:
        raise ValueError("Amount must be strictly positive (> 0).")

    # Check decimal places
    exponent = d.as_tuple().exponent
    if exponent < -2:
        raise ValueError(f"Amount '{s}' has more than 2 decimal places (fractional paise not supported).")

    # Calculate exact integer paise
    paise = int((d * Decimal(100)).to_integral_value())
    if paise <= 0:
        raise ValueError("Amount in paise must be positive.")

    return paise


def validate_date(date_str: str) -> str:
    """Validate ISO YYYY-MM-DD calendar date."""
    s = str(date_str).strip()
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        raise ValueError(f"Invalid date format '{s}'. Must be strict YYYY-MM-DD.")
    try:
        parsed = date.fromisoformat(s)
        # Re-format to ensure canonical YYYY-MM-DD
        return parsed.isoformat()
    except ValueError as e:
        raise ValueError(f"Invalid calendar date '{s}': {e}") from e


def validate_transaction_row(
    row: dict[str, str],
    row_num: Optional[int] = None,
) -> Transaction:
    """Validate a single dictionary row from CSV or manual entry form."""
    prefix = f"Row {row_num}: " if row_num is not None else ""

    # 1. ID
    tx_id = str(row.get("id", "")).strip()
    if not tx_id:
        raise ValueError(f"{prefix}Transaction ID cannot be empty.")
    if len(tx_id) > 100:
        raise ValueError(f"{prefix}Transaction ID exceeds 100 characters limit.")

    # 2. Date
    raw_date = row.get("date", "")
    validated_date = validate_date(raw_date)

    # 3. Description
    desc = " ".join(str(row.get("description", "")).strip().split())
    if not desc:
        raise ValueError(f"{prefix}Description cannot be empty.")
    if len(desc) > 300:
        raise ValueError(f"{prefix}Description exceeds 300 characters limit.")

    # 4. Amount
    raw_amount = row.get("amount", "")
    amount_paise = parse_amount_to_paise(raw_amount)

    # 5. Type
    tx_type = str(row.get("type", "")).strip().lower()
    if tx_type not in VALID_TYPES:
        raise ValueError(f"{prefix}Invalid transaction type '{tx_type}'. Must be 'income', 'expense', or 'transfer'.")

    # 6. Category
    raw_category = str(row.get("category", "")).strip()
    category_source = str(row.get("category_source", "imported")).strip() or "imported"
    review_status = str(row.get("review_status", "confirmed")).strip() or "confirmed"

    if tx_type == "income":
        category = "Income"
    elif tx_type == "transfer":
        category = "Transfer"
    else:  # expense
        if not raw_category:
            # Empty expense category indicates it should be suggested by AI
            category = ""
            category_source = "model"
            review_status = "needs_review"
        else:
            # Capitalize properly if needed
            matched_cat = next((c for c in ALLOWED_EXPENSE_CATEGORIES if c.lower() == raw_category.lower()), None)
            if not matched_cat:
                allowed_str = ", ".join(sorted(ALLOWED_EXPENSE_CATEGORIES))
                raise ValueError(f"{prefix}Invalid expense category '{raw_category}'. Allowed: {allowed_str}.")
            category = matched_cat

    fingerprint = compute_fingerprint(validated_date, desc, amount_paise, tx_type)

    raw_score = row.get("model_score")
    model_score: Optional[float] = None
    if raw_score not in (None, ""):
        try:
            model_score = float(raw_score)
        except ValueError:
            pass

    return Transaction(
        id=tx_id,
        date=validated_date,
        description=desc,
        amount_paise=amount_paise,
        type=tx_type,
        category=category,
        category_source=category_source,
        review_status=review_status,
        model_score=model_score,
        fingerprint=fingerprint,
    )


def parse_transactions_csv(content: str | bytes) -> tuple[list[Transaction], list[str]]:
    """Parse and atomically validate an uploaded CSV string or bytes.

    Returns:
        (transactions, errors):
        If any errors are encountered, transactions will be an empty list (atomic failure).
    """
    if isinstance(content, bytes):
        if len(content) > MAX_CSV_BYTES:
            return [], [f"File size exceeds maximum limit of {MAX_CSV_BYTES // (1024 * 1024)} MB."]
        try:
            # Handle UTF-8 and UTF-8-SIG (BOM)
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as e:
            return [], [f"CSV file must be UTF-8 encoded: {e}"]
    else:
        text = content
        if len(text.encode("utf-8")) > MAX_CSV_BYTES:
            return [], [f"File size exceeds maximum limit of {MAX_CSV_BYTES // (1024 * 1024)} MB."]

    reader = csv.reader(io.StringIO(text))
    rows = list(reader)

    if not rows:
        return [], ["CSV file is completely empty."]

    # Header validation
    raw_headers = [h.strip().lower() for h in rows[0]]
    if raw_headers != EXPECTED_HEADERS:
        expected_str = ",".join(EXPECTED_HEADERS)
        got_str = ",".join(raw_headers)
        return [], [f"Invalid CSV header. Expected: [{expected_str}], got: [{got_str}]"]

    data_rows = rows[1:]
    if len(data_rows) > MAX_CSV_ROWS:
        return [], [f"CSV exceeds maximum row limit of {MAX_CSV_ROWS} rows."]

    if not data_rows:
        return [], ["CSV contains header but no data rows."]

    errors: list[str] = []
    seen_ids: set[str] = set()
    transactions: list[Transaction] = []

    for idx, row_cells in enumerate(data_rows, start=2):
        if not any(c.strip() for c in row_cells):
            continue  # skip completely blank lines

        if len(row_cells) != len(EXPECTED_HEADERS):
            errors.append(f"Row {idx}: Expected {len(EXPECTED_HEADERS)} columns, found {len(row_cells)}.")
            continue

        row_dict = dict(zip(EXPECTED_HEADERS, row_cells))
        tx_id = row_dict["id"].strip()

        if tx_id in seen_ids:
            errors.append(f"Row {idx}: Duplicate ID '{tx_id}' found within the CSV file.")
            continue
        seen_ids.add(tx_id)

        try:
            tx = validate_transaction_row(row_dict, row_num=idx)
            transactions.append(tx)
        except ValueError as e:
            errors.append(str(e))

    if errors:
        # Atomic failure: return zero transactions if any validation error
        return [], errors

    return transactions, []
