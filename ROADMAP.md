# Development Roadmap — Student Finance Assistant

## Milestone 1: Core Financial Backend & Storage Engine
- **Objective:** Build robust, pure-Python modules for transactions, paise-based arithmetic, and SQLite persistence.
- **Deliverables:**
  - `src/transactions.py` (Validation, Decimal -> Paise, CSV parsing, fingerprinting)
  - `src/storage.py` (SQLite schema, atomic migrations, CRUD, demo data loader)
  - `src/analytics.py` (Paise sums, monthly filters, transfer exclusions, budget math, safe export)
  - Comprehensive unit tests in `tests/test_transactions.py`, `tests/test_storage.py`, `tests/test_analytics.py`
- **Success Criteria:** Independent verification that October and November demo totals match `data/demo/EXPECTED_TOTALS.json` to the exact paise.

## Milestone 2: AI Categorization & Evaluation Pipeline
- **Objective:** Implement the TF-IDF + Logistic Regression classification pipeline with vocabulary-based abstention and holdout evaluation.
- **Deliverables:**
  - `src/categorizer.py` (Pipeline fit, predict with confidence & OOV check, model caching)
  - `scripts/evaluate_model.py` (Evaluation runner producing `reports/model_evaluation.json`)
  - Unit tests in `tests/test_categorizer.py`
- **Success Criteria:** Zero data leakage from holdout dataset; all unknown/low-confidence inputs routed to "Other (Needs Review)"; honest reporting of precision/recall/F1 metrics.

## Milestone 3: Dribbble Nexora High-Fidelity UI Implementation
- **Objective:** Create the complete Streamlit interface matching the visual design brief in `handoff/DRIBBBLE_UI_PROMPT.md` and reference image `docs/ui-reference/reference.png`.
- **Deliverables:**
  - `.streamlit/config.toml` (Theme tokens: lavender backdrop, fonts, clean surfaces)
  - `app.py` (Complete UI with custom CSS, modern typography, responsive grid)
  - 4 Summary Metric Cards (Income, Expenses, Surplus, Transfers Excluded)
  - 70/30 Asymmetric Chart Row (Cumulative Income/Expense trend + Category Doughnut)
  - 30/70 Asymmetric Chart Row (Category Budgets progress + Mirrored Monthly comparison)
  - Functional views: Overview, Transactions, Budgets, Category Review, Model Evaluation
- **Success Criteria:** High visual match to the Dribbble reference, fully interactive controls, zero fake buttons.

## Milestone 4: Verification, Browser Testing & Real Screenshot Audit
- **Objective:** Run end-to-end tests, launch local Streamlit server, execute browser automation to capture real screenshots across desktop (1440x1000) and mobile (390px) viewports, and audit visual parity against `docs/ui-reference/reference.png`.
- **Deliverables:**
  - `docs/ui-implementation/desktop_dashboard.png`
  - `docs/ui-implementation/mobile_dashboard.png`
  - `docs/ui-implementation/transactions_view.png`
  - `docs/ui-implementation/budgets_view.png`
  - `docs/ui-implementation/category_review_view.png`
  - `tests/test_ui_smoke.py`
- **Success Criteria:** All unit and smoke tests passing; real browser screenshots saved and visually compared.

## Milestone 5: Quality Control & Academic Documentation
- **Objective:** Complete project reports, viva preparation guide, and clean codebase for submission.
- **Deliverables:**
  - `docs/PROJECT_REPORT.md` (Formal 3-4 page academic report)
  - `docs/VIVA_GUIDE.md` (Comprehensive viva defense guide covering algorithms, design trade-offs, and math)
  - Updated `README.md` and `docs/DEMO_SCRIPT.md`
- **Success Criteria:** Repository in a 100% reproducible, runnable state with complete documentation.
