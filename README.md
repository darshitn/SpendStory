# Student Finance Assistant — AI for Finance CIA-2

A local, privacy-first personal finance management application designed for university students. Track income, expenses, and category budgets in Indian Rupees (INR) with integer precision, explore explainable AI category suggestions with human-in-the-loop review, and enjoy a polished fintech interface matching the Dribbble "Nexora" Money Management Dashboard visual brief.

---

## Visual Design Reference
The user interface is modeled directly on the **Money Management Dashboard** design by Atiqur Rahman for ILmix Studio ([Dribbble Reference](https://dribbble.com/shots/27090441-Money-Management-Dashboard)).
- **Pale Lavender Canvas (`#E2E7F5`)**: High-contrast framing with rounded white application shell (`border-radius: 28px`).
- **Quiet Left Sidebar (`#F8FAFD`)**: Wordmark branding, thin line navigation items with live review count badges, and an idempotent Fictional Demo action card.
- **Four Financial Summary Cards**: Recorded Income, Recorded Expenses, Recorded Surplus, and Transfers Excluded.
- **Asymmetric Visualization Layout**:
  - *70/30 Row*: Truthful cumulative income/expense trend area chart beside an expense category doughnut chart with center total.
  - *30/70 Row*: Category budgets progress list with overspend alerts beside a mirrored monthly comparison bar chart.
- **Interactive Views**: Overview, Transactions (with search & inline category editing), Budgets (target allocations & rebalancing suggestions), Category Review (AI abstention queue), and Model Evaluation (live transparency metrics).

---

## Features & Mathematical Integrity
1. **Integer Paise Representation**: All monetary values are strictly parsed via `decimal.Decimal` and stored/summed as integer paise (1 INR = 100 paise) to eliminate floating-point rounding bugs.
2. **Transfer Exclusion**: Internal transfers between accounts (e.g. ATM cash withdrawals) are tracked but strictly excluded from income, expenses, and recorded surplus.
3. **Idempotent Ingestion**: SHA-256 payload fingerprinting prevents duplicate entries upon re-importing identical files while safeguarding user manual category corrections and detecting ID conflicts.
4. **Offline ML Categorization**: A scikit-learn TF-IDF + Logistic Regression pipeline trained on 72 student expenses. Implements vocabulary checks and confidence thresholds (0.25) to abstain to "Other (Needs Review)" on ambiguous or unknown descriptions.
5. **Spreadsheet Injection Defense**: CSV export prepends a single apostrophe (`'`) to any cell beginning with `=`, `+`, `-`, `@`, `\t`, or `\r`.
6. **100% Local & Offline**: Operates completely on local SQLite (`storage/finance.db`) without external API keys or cloud dependencies.

---

## Verified Demo Totals (`data/demo/transactions.csv`)
- **October 2026**:
  - Recorded Income: **₹15,000.00** (1,500,000 paise)
  - Recorded Expenses: **₹9,900.00** (990,000 paise)
  - Recorded Surplus: **₹5,100.00** (510,000 paise)
  - Transfers Excluded: **₹2,000.00** (200,000 paise)
- **November 2026**:
  - Recorded Income: **₹15,000.00** (1,500,000 paise)
  - Recorded Expenses: **₹8,340.00** (834,000 paise)
  - Recorded Surplus: **₹6,660.00** (666,000 paise)
  - Transfers Excluded: **₹2,000.00** (200,000 paise)

---

## Quickstart & Windows Commands

From the project root:

### 1. Environment & Dependencies
```powershell
# Activate or use existing Python 3.12 .venv
.\.venv\Scripts\python.exe -m pip check
```

### 2. Run Comprehensive Unit & Smoke Tests
```powershell
.\.venv\Scripts\python.exe -m pytest -q
```
*Executes all 27 tests covering validation, paise math, transfer exclusion, storage, ML abstention, and Streamlit AppTest UI smoke checks.*

### 3. Run Standalone Model Evaluation
```powershell
.\.venv\Scripts\python.exe scripts/evaluate_model.py
```
*Evaluates the offline model against untouched holdout data and updates `reports/model_evaluation.json`.*

### 4. Launch the Streamlit Application
```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```
*Open your browser at `http://127.0.0.1:8501`. On first run, click **Load Fictional Demo** in the sidebar to populate the verified October and November datasets.*

### 5. Automated Headless Browser Screen Captures
```powershell
.\.venv\Scripts\python.exe scripts/capture_screenshots.py
```
*Uses Chrome DevTools Protocol to capture real screenshots across desktop (1440x1000) and mobile (390x844) viewports into `docs/ui-implementation/`.*

---

## Project Structure
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
│   │   ├── desktop_dashboard.png
│   │   ├── mobile_dashboard.png
│   │   ├── transactions_view.png
│   │   ├── budgets_view.png
│   │   ├── category_review_view.png
│   │   └── model_evaluation_view.png
│   ├── PROJECT_SPEC.md
│   ├── PROJECT_REPORT.md     # Full academic project report
│   ├── VIVA_GUIDE.md         # Comprehensive viva defense guide
│   └── DEMO_SCRIPT.md        # 5-minute presentation walkthrough
├── handoff/
│   ├── ANTIGRAVITY_PROMPT.md
│   └── DRIBBBLE_UI_PROMPT.md
├── reports/
│   └── model_evaluation.json# Measured holdout evaluation metrics
├── scripts/
│   ├── evaluate_model.py     # Standalone holdout evaluation runner
│   └── capture_screenshots.py# CDP headless browser capture script
├── src/
│   ├── __init__.py
│   ├── analytics.py          # Paise math, budget comparisons, safe CSV
│   ├── categorizer.py        # ML pipeline, inference, abstention
│   ├── storage.py            # SQLite schema, queries, idempotent import
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

---

## Submission & Academic Disclosures
- **Fictional Data**: All sample transactions, merchants, and training data are synthetic.
- **Model Scope**: Holdout evaluation measures performance on this tiny synthetic corpus (27.8% accuracy, 72.2% abstention rate). It does not claim production bank statement parity.
- **Storage Security**: Local SQLite storage is plaintext; not encrypted at rest.
- **Assistance**: Antigravity (Google DeepMind) provided pair-programming and scaffolding assistance under human engineering supervision.
