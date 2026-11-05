# Student Finance Assistant — Architecture Specification

## 1. System Architecture
The application follows a modular, three-tier local architecture:
```
+-------------------------------------------------------------+
|             Frontend Presentation Layer (Streamlit)         |
|  - Nexora Shell Layout (Lavender backdrop, Rounded Frame)   |
|  - Sidebar Navigation, 4 Metric Cards, Custom Altair Charts |
|  - Views: Overview, Transactions, Budgets, AI Review, Eval   |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                     Application Service Layer               |
|  - transactions.py: Ingestion, Validation, Decimal->Paise   |
|  - analytics.py: Integer Math, Budgets, Aggregation, Export |
|  - categorizer.py: TF-IDF + LogisticRegression + Abstention |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                     Data Persistence Layer                  |
|  - storage.py: SQLite DB (storage/finance.db)               |
|  - Schema: transactions table, budgets table, audit metadata|
+-------------------------------------------------------------+
```

## 2. Frontend
- **Framework:** Streamlit 1.66.1 (`app.py`).
- **Styling Architecture:**
  - Modern sans-serif typography (`Inter`, system UI font fallback).
  - Pale lavender background (`#DCE2F4`) with a centered high-density rounded white app shell (`#FFFFFF`, `border-radius: 24px`, subtle shadow `0 20px 40px rgba(20, 24, 45, 0.08)`).
  - Quiet pale-gray sidebar (`#F7F8FA`) with clean line icons and active state highlights (`#4B5AEF`).
  - Asymmetric desktop grid:
    - Row 1: 4 equal summary metric cards (Recorded Income, Recorded Expenses, Recorded Surplus, Transfers Excluded).
    - Row 2: 70% Income & Expense cumulative trend line + 30% Expense category doughnut chart.
    - Row 3: 30% Category budget progress bars + 70% Mirrored monthly comparison column chart (Income positive, Expense negative magnitude).
  - Visual color palette:
    - Brand Primary: Indigo / Blue (`#373EDC` / `#4B5AEF`)
    - Secondary Accent: Violet / Magenta (`#993FC5` / `#D84DE6`)
    - Dark Text: Navy (`#14182D`)
    - Muted Text: Slate Gray (`#8E95A9`)
    - Surface Card Background: `#F8FAFC`
    - Borders: `#E2E8F0`
- **Charts:** Built with Altair 6.3.0 and Vega-Lite, customized with custom gradients, tooltips, and exact color mappings.

## 3. Backend Services
- **`src/transactions.py`:**
  - Strict CSV parsing: headers `id,date,description,amount,type,category`.
  - Amount validation: positive finite numbers, max 2 decimal places, converted strictly via `decimal.Decimal` to integer paise.
  - Type normalization: `income`, `expense`, `transfer`.
  - Content hashing: SHA-256 fingerprint generated from `(date, description, amount_paise, type)` to distinguish identical re-imports from conflicting ID collisions.
- **`src/analytics.py`:**
  - Integer paise aggregations: monthly income, monthly expenses, net surplus, transfer exclusions.
  - Category breakdown and percentage shares.
  - Budget calculations: spent vs budget, delta, overspend warning, and actionable recommendations.
  - Safe CSV exporter: prepends a single quote to cells beginning with formula injection characters (`=`, `+`, `-`, `@`, `\t`, `\r`).
- **`src/storage.py`:**
  - SQLite database abstraction.
  - Idempotent upsert logic with conflict detection.
  - Schema migration and fixture loading (atomic demo data population).

## 4. Database Schema
Stored in SQLite (`storage/finance.db` or in-memory for testing):
```sql
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

CREATE TABLE IF NOT EXISTS budgets (
    year_month TEXT NOT NULL,
    category TEXT NOT NULL,
    budget_paise INTEGER NOT NULL,
    PRIMARY KEY (year_month, category)
);
```

## 5. AI Components
- **Model Pipeline:** `sklearn.pipeline.Pipeline` with:
  1. `TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)`
  2. `LogisticRegression(C=1.0, max_iter=200, random_state=42)`
- **Training Data:** `data/training/categories.csv` (72 verified student transaction descriptions across 6 categories).
- **Abstention Engine:**
  - Checks if vocabulary overlap is zero or if maximum softmax probability < confidence threshold (default 0.40).
  - If abstained: category assigned is `Other`, `review_status = 'needs_review'`.
- **Holdout Evaluation:** Evaluated exclusively via `scripts/evaluate_model.py` against `data/evaluation/categories_holdout.csv` without data leakage.

## 6. Data Flow
1. **User Action (Upload CSV / Load Demo / Manual Entry):**
   - Ingestion validates row syntax, types, and paise conversion.
   - For uncategorized expense rows, `categorizer.py` generates predictions and confidence scores.
   - `storage.py` applies transactional insertion.
2. **Dashboard Query:**
   - Active month filter passed to `analytics.py`.
   - `analytics.py` executes SQL queries summing integer paise.
   - Formatted INR strings and Altair charts rendered in Streamlit UI.
3. **User Category Correction:**
   - User corrects an AI prediction in Category Review or Transactions view.
   - `storage.py` updates `category = new_cat`, `category_source = 'manual'`, `review_status = 'confirmed'`.
   - Subsequent re-imports of the same transaction fingerprint respect the manual correction.

## 7. Folder Structure
```
AI-For-Finance/
├── .streamlit/
│   └── config.toml           # Streamlit theme & server configuration
├── data/
│   ├── demo/
│   │   ├── EXPECTED_TOTALS.json
│   │   └── transactions.csv
│   ├── evaluation/
│   │   └── categories_holdout.csv
│   └── training/
│       └── categories.csv
├── docs/
│   ├── ui-reference/
│   │   └── reference.png      # Downloaded Dribbble reference image
│   ├── ui-implementation/   # Real browser screenshots
│   ├── PROJECT_SPEC.md
│   ├── PROJECT_REPORT.md
│   └── VIVA_GUIDE.md
├── handoff/
│   ├── ANTIGRAVITY_PROMPT.md
│   └── DRIBBBLE_UI_PROMPT.md
├── models/                    # Model serialization cache (ignored by git)
├── reports/                   # Evaluation output reports
├── scripts/
│   └── evaluate_model.py     # Standalone model evaluation CLI
├── src/
│   ├── __init__.py
│   ├── analytics.py          # Math, aggregates, budgets, suggestions
│   ├── categorizer.py        # ML pipeline, inference, abstention
│   ├── storage.py            # SQLite schema, queries, migrations
│   └── transactions.py       # Ingestion, validation, paise conversions
├── storage/
│   └── finance.db            # SQLite persistent store
├── tests/
│   ├── __init__.py
│   ├── test_analytics.py
│   ├── test_categorizer.py
│   ├── test_storage.py
│   ├── test_transactions.py
│   └── test_ui_smoke.py
├── app.py                     # Streamlit Dribbble Nexora application
├── ARCHITECTURE.md
├── AI_INSTRUCTIONS.md
├── PROJECT.md
├── README.md
├── ROADMAP.md
└── TASKS.md
```

## 8. Security & Privacy
- **Local Isolation:** No outbound telemetry or external API calls.
- **Formula Injection Defense:** Spreadsheets open exported CSVs without executing malicious commands.
- **SQL Injection Defense:** Parameterized SQL queries throughout `storage.py`.
- **Atomic Operations:** Database transactions wrapped in context managers ensuring no partial commits during CSV imports.

## 9. Important Technical Decisions
- **Integer Paise Representation:** All amounts are integers in storage and computation. Floating-point division only occurs at the final display step (`amount_paise / 100.0`).
- **Transfer Exclusion Rule:** Transfers are non-zero balance shifts between user accounts; they are excluded from Income, Expenses, and Net Surplus.
- **Offline ML Model:** Fast, deterministic, sub-second training on startup using scikit-learn; cached in memory with zero cloud footprint.
