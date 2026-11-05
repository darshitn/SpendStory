# Tasks Checklist — SpendStory Full UI Audit & Polish

## Phase 1: Shared App Shell & Interaction Language
- [x] Audit sidebar navigation and sticky toolbar at 1280px laptop and 390px mobile viewports
- [x] Fix sidebar label wrapping and demo button text wrapping at 1280px
- [x] Make toolbar controls contextual: hide search, month selector, and CSV buttons on Model Evaluation
- [x] Display real-time unreviewed badge in sidebar navigation (`Category Review (N)`)
- [x] Standardize typography, status badges, button variants, and surface treatments across all pages
- [x] Implement smooth 120–180ms hover/focus, 180–260ms panel entrances, and verify `@media (prefers-reduced-motion)`

## Phase 2: Overview Dashboard & Actionable Drill-Down
- [x] Refine 4 summary metric cards: clear green badge for positive surplus, distinct amber/red badge for deficit
- [x] Make Transfers Excluded card visually secondary with clear explanatory caption
- [x] Refine Trend Scrubber: single crisp marker, stable tooltip, reliable day labels, graceful handling of empty/1-date periods
- [x] Update Category Doughnut: add **"View transactions"** action for pinned category that opens Transactions with month, expense type, and pinned category selected
- [x] Verify Monthly Comparison bars: clickable month selection updating URL and state; selected-month band; animated expense reflection with positive magnitude tooltip
- [x] Enhance Budget Preview: show over-target alerts, link to full Budgets view, show truncation indicator ("Showing 5 of N categories"), and explicit "No target" label

## Phase 3: Transactions View & CSV Workflows
- [x] Implement denser, responsive ledger: tabular desktop view and clean mobile stacked cards
- [x] Truncate full transaction IDs with tooltip or detail view to prevent row wrapping
- [x] Add prominent "Add transaction" dialog/editor near header with inline validation and AI suggestion option
- [x] Consolidate filter bar: Search, Type, Category, and Review Status with result count and 1-click reset
- [x] Accept and apply incoming Category drill-down from Overview doughnut on initial render
- [x] Implement safe row deletion with confirmation modal/dialog and single final database write
- [x] Streamline CSV import: file selection, schema guidance, preview before commit, and duplicate protection
- [x] Ensure safe CSV export with formula injection escaping

## Phase 4: Budgets View Deep Polish
- [x] Unify category budget layout: target, actual spend, remaining amount, and status together at a single glance
- [x] Provide inline edit affordance with explicit Save and Cancel; atomic multi-category persistence
- [x] Differentiate "No target" from intentional ₹0 budget; prevent draft values leaking between months
- [x] Build bounded progress bars with matching labels and clear over-target indicators
- [x] Display deterministic spending adjustment suggestions based on computed category deltas

## Phase 5: Category Review Queue
- [x] Provide explicit queue count and scope selector (Current Month vs All Records)
- [x] Align sidebar navigation badge with active queue count
- [x] Populate review cards: description, date, amount, current suggestion, uncalibrated model score, and plain-language explanation
- [x] Implement explicit confirmation and manual correction buttons preserving `category_source="manual"`
- [x] Provide skip and inspect actions without accidental confirmation
- [x] Build clean empty queue state and support synthetic review queue fixtures

## Phase 6: Model Evaluation & Transparency
- [x] Restyle Model Evaluation to match the lavender visual theme (lavender frame, white cards, elegant metrics)
- [x] Add clear disclaimer stating evaluation is offline on synthetic held-out examples independent of the finance month
- [x] Display readable metrics: training/holdout counts, overall accuracy, coverage, abstention rate
- [x] Render formatted comparison table/graphic replacing raw JSON/grid
- [x] Provide expandable explanations for technical limitations and friendly recovery command (`python scripts/evaluate_model.py`)

## Phase 7: Verification, Automated Browser Captures & Acceptance
- [x] Configure isolated preview server on a free port (e.g. 8502 or 8515) with temporary SQLite database
- [x] Load fictional demo data (`data/demo/transactions.csv`) into temporary database
- [x] Verify exact October 2026 totals: Income ₹15,000, Expenses ₹9,900, Surplus ₹5,100, Transfers ₹2,000
- [x] Write targeted pytest tests for drill-down routing, budget state persistence, and CSV security
- [x] Run complete pytest suite and verify 100% pass rate
- [x] Update `scripts/capture_screenshots.py` to target isolated preview port and capture:
  - [x] Desktop dashboard (1440×1000)
  - [x] Laptop dashboard (1280×800)
  - [x] Mobile dashboard (390px)
  - [x] Transactions view (with filtered ledger and add form)
  - [x] Budgets view (with overspend and targets)
  - [x] Category Review view (populated queue and empty state)
  - [x] Model Evaluation view
  - [x] Chart interaction / tooltip highlight
- [x] Review captured screenshots against visual references and verify zero defects
- [x] Commit milestones to Git with clean commit history
- [x] Provide complete acceptance report with browser evidence
