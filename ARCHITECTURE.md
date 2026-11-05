# SpendStory — Architecture Specification

## 1. System Architecture
The application follows a modular, three-tier local architecture:
```
+-------------------------------------------------------------+
|             Frontend Presentation Layer (Streamlit)         |
|  - Nexora Shell Layout (Lavender backdrop, Rounded Frame)   |
|  - Sticky Contextual Toolbar (Search, Month, Import, Export)|
|  - Quiet Sidebar Navigation with Active Review Badge        |
|  - Custom SVG Charts (Trend Scrubber, Donut, Monthly Mirror)|
|  - Views: Overview, Transactions, Budgets, AI Review, Eval   |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                     Application Service Layer               |
|  - transactions.py: Ingestion, Validation, Decimal->Paise   |
|  - analytics.py: Integer Math, Budgets, Aggregation, Export |
|  - categorizer.py: TF-IDF + LogisticRegression + Abstention |
|  - dashboard_charts.py: Streamlit V2 SVG Component Bridge   |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                     Data Persistence Layer                  |
|  - storage.py: SQLite DB (storage/finance.db or env path)   |
|  - Schema: transactions table, budgets table, audit metadata|
+-------------------------------------------------------------+
```

## 2. Frontend Architecture
- **Framework:** Streamlit 1.66.1 (`app.py`).
- **Styling & Layout:**
  - Injected Scoped CSS (`NEXORA_CSS`).
  - Lavender backdrop (`linear-gradient(161deg, #d7def8 7%, #dedcf8 53%, #e8d1f3 100%)`).
  - Rounded white application shell (`#FFFFFF`, `border-radius: 23px`, box shadow with multi-layer borders).
  - Quiet pale-gray sidebar (`#F8FAFD`, `border-right: 1px solid #EDF1F7`).
  - Desktop responsive shell with `min-width: 901px` flex layout, sticky toolbar, and clean mobile reflow (`@media (max-width: 900px)` and `@media (max-width: 640px)`).
  - High-density typography (`Inter`, -apple-system, sans-serif) and tabular numeric figures (`font-variant-numeric: tabular-nums`).
- **Interactive SVG Charts (`src/dashboard_charts.py`, `dashboard_charts.js`, `dashboard_charts.css`):**
  - Managed via `st.components.v2.component("nexora_dashboard_chart", ...)`.
  - **Trend Scrubber:** Timeline scrubber with interactive crosshair, date highlight band, unstacked gradient fills, and exact tooltip amounts.
  - **Category Doughnut:** Donut arc chart with centered total amount, callout lines, synchronized legend buttons, pinned slice highlight, and **"View transactions"** drill-down trigger.
  - **Monthly Comparison:** Mirrored column chart with positive income bars and negative expense reflection with ripple animation; interactive month selection updating the active session state and URL query parameters.
- **Motion & Accessibility:**
  - Micro-interactions: 120–180ms hover/focus/tooltip transitions.
  - Entrance animations: 180–260ms panel and metric counter reveals.
  - Initial chart reveal: 350–500ms SVG clip/dash reveal on load.
  - Strict `@media (prefers-reduced-motion: reduce)` disabling animations, transitions, and ripple effects.

## 3. Backend & Service Layer
- **`src/transactions.py`:**
  - Strict CSV parsing and schema validation (`id,date,description,amount,type,category`).
  - Safe conversion from decimal string representation to exact integer paise (1 INR = 100 paise).
  - SHA-256 fingerprint generation (`date + description + amount_paise + type`) for duplicate checking.
- **`src/storage.py`:**
  - SQLite database management using `sqlite3` with `PRAGMA foreign_keys = ON; PRAGMA journal_mode = WAL;`.
  - Configurable database path via `FINANCE_DB_PATH` environment variable (defaults to `storage/finance.db`).
  - Transaction CRUD, category budget CRUD, atomic multi-record saving, and idempotent demo data loading.
- **`src/analytics.py`:**
  - Strict integer paise aggregations: Income, Expenses, Recorded Surplus (`income - expense`), and Transfers Excluded.
  - Budget delta calculations, overspend identification, and deterministic rebalancing suggestions.
  - Formula injection safe CSV export (prepending `'` to cells beginning with `=`, `+`, `-`, or `@`).
- **`src/categorizer.py`:**
  - TF-IDF feature extraction + Logistic Regression classification.
  - Confidence scoring and out-of-vocabulary (OOV) heuristic routing low-confidence transactions to `Other` with `review_status="needs_review"`.
  - Respects manual corrections (`category_source="manual"`).

## 4. Database Schema
```sql
CREATE TABLE IF NOT EXISTS transactions (
    id TEXT PRIMARY KEY,
    date TEXT NOT NULL,
    description TEXT NOT NULL,
    amount_paise INTEGER NOT NULL,
    type TEXT NOT NULL CHECK(type IN ('income', 'expense', 'transfer')),
    category TEXT NOT NULL,
    category_source TEXT NOT NULL CHECK(category_source IN ('manual', 'model', 'import')),
    review_status TEXT NOT NULL CHECK(review_status IN ('confirmed', 'needs_review')),
    model_score REAL,
    fingerprint TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS budgets (
    year_month TEXT NOT NULL,
    category TEXT NOT NULL,
    amount_paise INTEGER NOT NULL,
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (year_month, category)
);
```

## 5. Security & Isolation
- **Environment Isolation:** Testing and screenshot capture run against a dedicated temporary SQLite database (`FINANCE_DB_PATH`) on an isolated localhost port (e.g. 8502 or 8515) to prevent modifying production state.
- **Formula Injection Mitigation:** All CSV exports sanitize text fields to prevent spreadsheet formula execution vulnerabilities.
- **Zero Remote Dependencies:** Operates 100% locally with zero cloud API keys or telemetry.
