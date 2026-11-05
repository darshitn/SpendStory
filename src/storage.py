"""SQLite storage layer for transactions, categories, and budgets.

Supports schema migrations, idempotent batch ingestion with SHA-256 fingerprinting,
safe category updates, and budget management.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
import sqlite3
from typing import Optional

from src.transactions import Transaction, parse_transactions_csv


@dataclass(frozen=True)
class ImportResult:
    inserted: int
    skipped: int
    conflicts: list[str]

    @property
    def total_processed(self) -> int:
        return self.inserted + self.skipped + len(self.conflicts)


class Database:
    def __init__(self, db_path: str = "storage/finance.db") -> None:
        self.db_path = db_path
        self._memory_conn: Optional[sqlite3.Connection] = None
        if db_path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        else:
            self._memory_conn = sqlite3.connect(":memory:", check_same_thread=False)
            self._memory_conn.row_factory = sqlite3.Row
            self._memory_conn.execute("PRAGMA foreign_keys = ON;")
        self._init_schema()

    def get_connection(self) -> sqlite3.Connection:
        if self._memory_conn is not None:
            return self._memory_conn
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def _init_schema(self) -> None:
        with self.get_connection() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS transactions (
                    id TEXT PRIMARY KEY,
                    date TEXT NOT NULL,
                    description TEXT NOT NULL,
                    amount_paise INTEGER NOT NULL,
                    type TEXT NOT NULL CHECK(type IN ('income', 'expense', 'transfer')),
                    category TEXT NOT NULL,
                    category_source TEXT NOT NULL CHECK(category_source IN ('imported', 'manual', 'model')),
                    review_status TEXT NOT NULL CHECK(review_status IN ('confirmed', 'needs_review')),
                    model_score REAL,
                    fingerprint TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
                CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type);
                CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category);

                CREATE TABLE IF NOT EXISTS budgets (
                    year_month TEXT NOT NULL,
                    category TEXT NOT NULL,
                    budget_paise INTEGER NOT NULL,
                    PRIMARY KEY (year_month, category)
                );
                """
            )

    def save_transactions(self, transactions: list[Transaction]) -> ImportResult:
        """Atomically save transactions with idempotent deduplication.

        Rules:
        - If ID does not exist: insert transaction.
        - If ID exists and fingerprint matches: SKIP (duplicate import; preserve user modifications).
        - If ID exists and fingerprint differs: CONFLICT (same ID reused for different data; reject row).
        """
        inserted = 0
        skipped = 0
        conflicts: list[str] = []

        now_iso = datetime.now(timezone.utc).isoformat()

        with self.get_connection() as conn:
            cursor = conn.cursor()
            for tx in transactions:
                cursor.execute(
                    "SELECT fingerprint, category, category_source, review_status FROM transactions WHERE id = ?",
                    (tx.id,),
                )
                row = cursor.fetchone()
                if row is None:
                    # New record
                    cursor.execute(
                        """
                        INSERT INTO transactions (
                            id, date, description, amount_paise, type, category,
                            category_source, review_status, model_score, fingerprint, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            tx.id,
                            tx.date,
                            tx.description,
                            tx.amount_paise,
                            tx.type,
                            tx.category,
                            tx.category_source,
                            tx.review_status,
                            tx.model_score,
                            tx.fingerprint,
                            now_iso,
                        ),
                    )
                    inserted += 1
                else:
                    stored_fingerprint = row["fingerprint"]
                    if stored_fingerprint == tx.fingerprint:
                        # Identical payload: skip and preserve existing row
                        skipped += 1
                    else:
                        # Conflicting payload for existing ID
                        conflicts.append(
                            f"Transaction ID '{tx.id}' already exists with different details. "
                            f"Existing: '{stored_fingerprint[:8]}...', New: '{tx.fingerprint[:8]}...'"
                        )

            conn.commit()

        return ImportResult(inserted=inserted, skipped=skipped, conflicts=conflicts)

    def add_transaction(self, tx: Transaction) -> bool:
        """Insert a single transaction. Raises ValueError if ID already exists."""
        now_iso = datetime.now(timezone.utc).isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM transactions WHERE id = ?", (tx.id,))
            if cursor.fetchone() is not None:
                raise ValueError(f"Transaction ID '{tx.id}' already exists.")
            cursor.execute(
                """
                INSERT INTO transactions (
                    id, date, description, amount_paise, type, category,
                    category_source, review_status, model_score, fingerprint, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tx.id,
                    tx.date,
                    tx.description,
                    tx.amount_paise,
                    tx.type,
                    tx.category,
                    tx.category_source,
                    tx.review_status,
                    tx.model_score,
                    tx.fingerprint,
                    now_iso,
                ),
            )
            conn.commit()
            return True

    def update_transaction_category(
        self,
        tx_id: str,
        new_category: str,
        review_status: str = "confirmed",
        category_source: str = "manual",
    ) -> bool:
        """Update transaction category manually by user."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE transactions
                SET category = ?, category_source = ?, review_status = ?
                WHERE id = ?
                """,
                (new_category, category_source, review_status, tx_id),
            )
            conn.commit()
            return cursor.rowcount > 0

    def delete_transaction(self, tx_id: str) -> bool:
        """Delete a transaction by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_transaction(self, tx_id: str) -> Optional[Transaction]:
        """Fetch a single transaction by ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, date, description, amount_paise, type, category,
                       category_source, review_status, model_score, fingerprint
                FROM transactions WHERE id = ?
                """,
                (tx_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return Transaction(
                id=row["id"],
                date=row["date"],
                description=row["description"],
                amount_paise=row["amount_paise"],
                type=row["type"],
                category=row["category"],
                category_source=row["category_source"],
                review_status=row["review_status"],
                model_score=row["model_score"],
                fingerprint=row["fingerprint"],
            )

    def get_transactions(
        self,
        year_month: Optional[str] = None,
        category: Optional[str] = None,
        tx_type: Optional[str] = None,
        review_status: Optional[str] = None,
        search_query: Optional[str] = None,
    ) -> list[Transaction]:
        """Query transactions with optional filtering and search."""
        clauses = []
        params: list[object] = []

        if year_month:
            clauses.append("substr(date, 1, 7) = ?")
            params.append(year_month)

        if category:
            clauses.append("category = ?")
            params.append(category)

        if tx_type:
            clauses.append("type = ?")
            params.append(tx_type)

        if review_status:
            clauses.append("review_status = ?")
            params.append(review_status)

        if search_query:
            clauses.append("(description LIKE ? OR id LIKE ?)")
            q = f"%{search_query.strip()}%"
            params.extend([q, q])

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        query = f"""
            SELECT id, date, description, amount_paise, type, category,
                   category_source, review_status, model_score, fingerprint
            FROM transactions
            {where_sql}
            ORDER BY date DESC, id DESC
        """

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()

            return [
                Transaction(
                    id=r["id"],
                    date=r["date"],
                    description=r["description"],
                    amount_paise=r["amount_paise"],
                    type=r["type"],
                    category=r["category"],
                    category_source=r["category_source"],
                    review_status=r["review_status"],
                    model_score=r["model_score"],
                    fingerprint=r["fingerprint"],
                )
                for r in rows
            ]

    def get_available_months(self) -> list[str]:
        """Return list of YYYY-MM strings present in transactions, sorted descending."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT substr(date, 1, 7) AS ym FROM transactions ORDER BY ym DESC")
            return [row["ym"] for row in cursor.fetchall() if row["ym"]]

    def set_budget(self, year_month: str, category: str, budget_paise: int) -> None:
        """Set or update the budget in paise for a category in a month."""
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO budgets (year_month, category, budget_paise)
                VALUES (?, ?, ?)
                ON CONFLICT(year_month, category) DO UPDATE SET budget_paise = excluded.budget_paise
                """,
                (year_month, category, budget_paise),
            )
            conn.commit()

    def delete_budget(self, year_month: str, category: str) -> bool:
        """Remove a budget target for a category in a month (sets to No Target)."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM budgets WHERE year_month = ? AND category = ?",
                (year_month, category),
            )
            conn.commit()
            return cursor.rowcount > 0

    def get_budgets(self, year_month: str) -> dict[str, int]:
        """Return dict of {category: budget_paise} for a given month."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT category, budget_paise FROM budgets WHERE year_month = ? ORDER BY category ASC",
                (year_month,),
            )
            return {row["category"]: row["budget_paise"] for row in cursor.fetchall()}

    def clear_all_data(self) -> None:
        """Clear all transactions and budgets."""
        with self.get_connection() as conn:
            conn.execute("DELETE FROM transactions;")
            conn.execute("DELETE FROM budgets;")
            conn.commit()

    def load_demo_data(self, demo_csv_path: str = "data/demo/transactions.csv") -> ImportResult:
        """Idempotently load the supplied demo transactions and set standard budgets."""
        p = Path(demo_csv_path)
        if not p.exists():
            raise FileNotFoundError(f"Demo CSV not found at '{demo_csv_path}'")

        content = p.read_bytes()
        transactions, errors = parse_transactions_csv(content)
        if errors:
            raise ValueError(f"Failed to parse demo CSV: {'; '.join(errors)}")

        res = self.save_transactions(transactions)

        # Standard default budgets for student demo
        default_budgets = {
            "Food": 200000,          # INR 2,000
            "Transport": 100000,     # INR 1,000
            "Shopping": 150000,      # INR 1,500
            "Education": 150000,     # INR 1,500
            "Bills": 300000,         # INR 3,000
            "Entertainment": 80000,  # INR 800
        }

        for ym in ["2026-10", "2026-11"]:
            for cat, amount in default_budgets.items():
                # Only insert if no budget already set
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT budget_paise FROM budgets WHERE year_month = ? AND category = ?",
                        (ym, cat),
                    )
                    if cursor.fetchone() is None:
                        self.set_budget(ym, cat, amount)

        return res
