# Development Roadmap — SpendStory Full UI Audit & Polish

## Phase 1: Shared App Shell & Interaction Language
- **Objective:** Establish rock-solid visual consistency, responsive layout, and clean interaction states across all five views.
- **Key Deliverables:**
  - Audit sidebar and sticky toolbar at 1280px laptop and 390px mobile viewports; fix label and demo button wrapping.
  - Make toolbar controls strictly contextual: hide search, month selector, and CSV actions on Model Evaluation; preserve on Overview, Transactions, and Budgets.
  - Implement real-time unreviewed badge in sidebar navigation (`Category Review (N)`).
  - Unify button styling, status badges, typography, and card surfaces across all pages.
  - Standardize motion timings (120–180ms hover/focus, 180–260ms panel entrances, 300–500ms chart reveals) and verify `@media (prefers-reduced-motion)`.

## Phase 2: Overview Dashboard & Actionable Drill-Down
- **Objective:** Refine the high-fidelity Overview dashboard with clear deficit indication, improved chart interactions, and direct transaction drill-down.
- **Key Deliverables:**
  - Summary cards: distinct visual treatment for positive surplus vs deficit (amber/red badge for negative surplus) and secondary styling for transfers.
  - Trend Scrubber: single crisp marker, stable tooltip, reliable day labels, graceful handling of empty/1-date/multi-date periods.
  - Category Doughnut: pinned slice highlight with explicit **"View transactions"** action that switches to Transactions with active month, expense type, and pinned category selected.
  - Monthly Comparison: clickable bars updating month and URL state; selected-month highlight band; animated expense reflection with positive magnitude in tooltip.
  - Budget Preview: actionable preview with over-target alerts, link to full Budgets view, truncation notice ("Showing 5 of N categories"), and explicit "No target" label.

## Phase 3: Transactions View & CSV Workflows
- **Objective:** Deliver a dense, responsive transaction ledger with streamlined editing, safe deletion, and robust CSV flows.
- **Key Deliverables:**
  - Dense responsive ledger with tabular desktop view and clean mobile cards.
  - Prominent "Add transaction" dialog/editor near header with inline validation and AI suggestion option.
  - Consolidated filter area (Search, Type, Category, Review Status) with result counts, active filter chips, and 1-click reset.
  - Full IDs displayed in details/tooltips rather than wrapping in main table rows.
  - Safe deletion workflow with confirmation naming the record and Cancel path.
  - Atomic CSV import with preview, error feedback, and duplicate protection.
  - Safe CSV export with formula injection escaping.

## Phase 4: Budgets View Deep Polish
- **Objective:** Unify category budget targets, actual spend, remaining amounts, and recommendations into a scannable, cohesive interface.
- **Key Deliverables:**
  - Consolidated category card layout combining target, spend, remaining balance, and status.
  - Inline edit affordances with explicit Save and Cancel; atomic multi-category persistence.
  - Explicit distinction between "No target" and intentional ₹0 budget; draft preservation without leaking between months.
  - Bounded progress bars showing exact overage without visual clipping.
  - Deterministic spending suggestions tied to computed category differences.

## Phase 5: Category Review Queue
- **Objective:** Streamline the AI review workflow with explicit queue scoping, plain-language explanations, and clear confirmation.
- **Key Deliverables:**
  - Explicit queue count and scope selector (Current Month vs All Records).
  - Synchronized sidebar badge count.
  - Card layout with description, date, amount, current suggestion, uncalibrated model score, and plain-language reason for review.
  - Explicit confirmation and manual category correction preserving `category_source="manual"`.
  - Skip and inspect options without accidental confirmation.
  - Graceful empty queue state and synthetic review queue fixtures.

## Phase 6: Model Evaluation & Transparency
- **Objective:** Elevate the Model Evaluation page to match the lavender visual system with plain-language metrics and accessible comparisons.
- **Key Deliverables:**
  - Visual styling aligned with Overview (lavender container, white cards, elegant metrics).
  - Prominent disclosure that evaluation operates on synthetic held-out examples independent of the finance month.
  - Plain-language metrics: overall accuracy, coverage, abstention rate, and per-category support.
  - Formatted comparison table/graphic replacing raw JSON/grid.
  - Expandable explanations for technical details and friendly recovery message with CLI command.

## Phase 7: Verification, Automated Browser Captures & Acceptance
- **Objective:** Verify end-to-end functionality, execute complete test suite, and capture real browser evidence across all views and viewports.
- **Key Deliverables:**
  - Isolated preview running on dedicated port (e.g. 8502 or 8515) with temporary SQLite database.
  - Validate exact October 2026 demo totals: Income ₹15,000, Expenses ₹9,900, Surplus ₹5,100, Transfers ₹2,000.
  - Pytest suite passing with new regression tests for drill-downs and budget logic.
  - Chrome CDP browser automation capturing all 5 views at 1440×1000, 1280×800, and 390px.
  - Verification of reduced-motion mode and empty states.
  - Complete acceptance report with browser evidence.
