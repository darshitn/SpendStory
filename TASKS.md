# Tasks List — Student Finance Assistant

## Milestone 1: Core Financial Backend & Storage Engine
- [ ] Create `src/__init__.py` and `tests/__init__.py`
- [ ] Implement `src/transactions.py` (Validation, Decimal -> Paise conversion, CSV parsing, SHA-256 fingerprinting)
- [ ] Implement `src/storage.py` (SQLite connection, schema migration, transaction CRUD, budget CRUD, idempotent demo loader)
- [ ] Implement `src/analytics.py` (Integer paise math, monthly aggregations, transfer exclusions, budget deltas, suggestions, safe CSV export)
- [ ] Write unit tests: `tests/test_transactions.py`
- [ ] Write unit tests: `tests/test_storage.py`
- [ ] Write unit tests: `tests/test_analytics.py`
- [ ] Run pytest to verify all Milestone 1 tests pass and exact demo totals match `EXPECTED_TOTALS.json`
- [ ] Git checkpoint commit for Milestone 1

## Milestone 2: AI Categorizer & Evaluation Pipeline
- [ ] Implement `src/categorizer.py` (TF-IDF + Logistic Regression, confidence score, OOV check, abstention mechanism)
- [ ] Implement `scripts/evaluate_model.py` (Holdout evaluation, confusion matrix, JSON report output)
- [ ] Write unit tests: `tests/test_categorizer.py`
- [ ] Execute `scripts/evaluate_model.py` and generate `reports/model_evaluation.json`
- [ ] Run pytest across all test suites
- [ ] Git checkpoint commit for Milestone 2

## Milestone 3: High-Fidelity UI Implementation (Dribbble Nexora Theme)
- [ ] Configure `.streamlit/config.toml` (Base theme, colors, font settings)
- [ ] Build `app.py` structure (Session state initialization, router, layout engine)
- [ ] Inject custom scoped CSS for the Dribbble Nexora look & feel (pale lavender `#DCE2F4`, rounded white app shell, quiet sidebar `#F7F8FA`, compact header)
- [ ] Implement Overview Dashboard:
  - [ ] 4 equal financial summary cards (Income, Expenses, Surplus, Transfers Excluded)
  - [ ] 70/30 row: Cumulative Income/Expense trend line chart + Category Doughnut chart
  - [ ] 30/70 row: Monthly category budgets progress bars + Mirrored Monthly Comparison chart
- [ ] Implement Transactions View (Search bar, month filter, category filter, pagination/list, manual transaction form, inline category editor)
- [ ] Implement Budgets View (Monthly budget manager, progress indicators, overspend alerts, deterministic recommendations)
- [ ] Implement Category Review View (Unreviewed AI predictions, confidence indicators, batch/individual confirmation & correction)
- [ ] Implement Model Evaluation View (Display offline training metrics, holdout confusion matrix, abstention counts)
- [ ] Implement CSV Ingestion & Demo Data Controls (Preview before atomic commit, duplicate checking, clear data with confirmation)
- [ ] Write UI smoke tests in `tests/test_ui_smoke.py`
- [ ] Git checkpoint commit for Milestone 3

## Milestone 4: Verification, Browser Screen Captures & Visual Audit
- [ ] Run Streamlit app in headless background mode
- [ ] Verify HTTP 200 health response at `http://127.0.0.1:8501`
- [ ] Use headless Chrome/Edge to capture real screenshots:
  - [ ] Desktop dashboard (1440x1000) -> `docs/ui-implementation/desktop_dashboard.png`
  - [ ] Mobile dashboard (390x844) -> `docs/ui-implementation/mobile_dashboard.png`
  - [ ] Transactions view -> `docs/ui-implementation/transactions_view.png`
  - [ ] Budgets view -> `docs/ui-implementation/budgets_view.png`
  - [ ] Category review view -> `docs/ui-implementation/category_review_view.png`
- [ ] Visually compare screenshots with `docs/ui-reference/reference.png` and tune CSS/visual details
- [ ] Stop background test server
- [ ] Git checkpoint commit for Milestone 4

## Milestone 5: Quality Control, Reports & Documentation
- [ ] Perform full code quality review (anti-patterns, security, performance, typing)
- [ ] Generate comprehensive `docs/PROJECT_REPORT.md` (3-4 pages academic report)
- [ ] Generate `docs/VIVA_GUIDE.md` (Detailed Q&A viva defense preparation)
- [ ] Update `README.md` with complete installation, usage, and visual documentation
- [ ] Update `docs/DEMO_SCRIPT.md` with step-by-step 5-minute presentation script
- [ ] Run full test suite (`pytest -q`, `pip check`, `scripts/evaluate_model.py`)
- [ ] Final Git checkpoint commit
