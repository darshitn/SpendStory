# SpendStory — Project Specification & Discovery

## Problem
University students and young adults frequently struggle to maintain financial discipline and understand their monthly cash outflow. Existing solutions suffer from key issues:
1. They require live bank/UPI account linking or credentials, creating privacy and security risks.
2. They are bloated with credit score tracking, loan advertisements, investments, and complex multi-currency wallets.
3. They use standard floating-point arithmetic leading to precision errors in financial accounting.
4. They rely on manual tagging for every expense, which causes tracking fatigue, or they use opaque cloud AI models that hallucinate spending categories.
5. Desktop interfaces frequently break down at common laptop viewports (1280px) and mobile screens (390px), with awkward label wrapping, disconnected filters, and non-actionable chart summaries.

Students need a fast, local, privacy-respecting financial assistant that answers three core questions:
- *Where did my recorded money go this month?*
- *Which category budgets did I exceed?*
- *What specific spending adjustments will bring me back within target?*

## Target Users
- **Primary Audience:** College students and young adults managing monthly stipends, allowances, or part-time earnings in Indian Rupees (INR).
- **Usage Environment:** Local desktop/laptop application requiring zero cloud connectivity, zero API keys, and complete data sovereignty. Viewport support spans desktop (1440×1000), compact laptop (1280×800), and mobile smartphones (390px).

## Project Goals
1. **Mathematical Accuracy:** Store and calculate all monetary quantities using integer paise (1 INR = 100 paise) to eliminate floating-point representation and rounding anomalies.
2. **Transparent AI Categorization:** Provide an explainable, local machine learning model (TF-IDF + Logistic Regression) that assists with categorizing expenses, handles vocabulary gaps with explicit abstention ("needs review"), and never overrides manual user corrections.
3. **High-Fidelity Visual Design:** Implement the exact layout, density, typography, and lavender aesthetic inspired by the Dribbble "Nexora" Money Management Dashboard reference (`docs/ui-reference/reference.png` and `handoff/DRIBBBLE_UI_PROMPT.md`), extended across all five core pages.
4. **Seamless Actionable Flow:** Connect interactive charts (e.g. Overview category doughnut) directly to transaction records with 1-click drill-downs, contextual page controls, and explicit queue management.
5. **Resilient Data Integrity:** Enforce atomic CSV imports, SHA-256 fingerprinting for idempotent re-imports, duplicate ID detection within uploads, safe formula-injection-resistant CSV export, and persistent SQLite storage.

## Core Features
1. **Shared App Shell & Responsive Layout:**
   - Pale lavender outer frame (`#DCE2F4`) with high-density rounded white app container (`border-radius: 24px`).
   - Sticky top toolbar with page-specific contextual controls (search and month where applicable; hidden on dataset-wide Model Evaluation).
   - Quiet left sidebar with active state highlights, real-time unreviewed badge count (`Category Review (N)`), and non-wrapping buttons at 1280px.
   - Smooth 120–180ms hover transitions, 180–260ms panel entrances, and 300–500ms chart reveals with strict `prefers-reduced-motion` overrides.
2. **Overview Dashboard:**
   - 4 equal financial summary cards: Recorded Income, Recorded Expenses, Recorded Surplus (with distinct positive surplus vs negative deficit badge), and Transfers Excluded.
   - 70/30 main chart split: Cumulative Income vs Expense trend line (with crisp scrubber, tooltip, and day labels) beside an Expense Category Doughnut chart.
   - Pinned category doughnut slice with direct **"View transactions"** 1-click drill-down to filtered Transactions.
   - 30/70 secondary chart split: Actionable Category Budgets preview (with over-budget alerts and link to full budget manager) beside a Mirrored Monthly Comparison column chart (Income positive, Expense negative magnitude reflection).
3. **Transactions & CSV Management:**
   - Dense responsive ledger with tabular desktop view and readable stacked mobile cards.
   - Prominent "Add transaction" dialog/editor near the header with inline validation and AI suggestion option.
   - Consolidated filter bar (Search, Type, Category, Review Status) with result counts and 1-click reset.
   - Safe row deletion with confirmation modal/dialog and single final write.
   - Robust CSV import with staging preview, error diagnostics, and duplicate detection. Safe CSV export with formula injection escaping.
4. **Budgets & Rebalancing Engine:**
   - Unified category cards showing target, actual spend, remaining amount, and status together at a single glance.
   - Direct edit affordances with explicit Save/Cancel, atomic multi-category persistence, and clear distinction between "No target" and intentional ₹0 target.
   - Animated progress bars with agreeing labels, bounded over-target displays, and deterministic adjustment recommendations.
5. **Category Review Queue:**
   - Explicit queue count and scope selector (Current Month vs All Records).
   - Plain-language explanations for review requirements (low confidence, out-of-vocabulary terms) and uncalibrated model scores.
   - Explicit confirmation and correction flow preserving manual provenance (`category_source="manual"`).
6. **Model Evaluation & Transparency:**
   - Visual styling aligned with Overview (lavender container, white cards, elegant metrics).
   - Clear disclosure that metrics reflect offline evaluation on synthetic held-out examples.
   - Formatted percentages, visible support counts, confusion matrix summary, and CLI recovery command.

## MVP Scope
- Single-user local deployment via Streamlit on localhost.
- Local SQLite database in `storage/finance.db` (or temporary database via `FINANCE_DB_PATH`).
- Supported expense categories: `Food`, `Transport`, `Shopping`, `Education`, `Bills`, `Entertainment`, `Other`.
- Fixed synthetic demo dataset with exact expected totals:
  - October 2026: ₹15,000 Income, ₹9,900 Expenses, ₹5,100 Surplus (₹2,000 Transfer excluded).
  - November 2026: ₹15,000 Income, ₹8,340 Expenses, ₹6,660 Surplus (₹2,000 Transfer excluded).
- Fully interactive Dribbble Nexora UI reproduction across all 5 views with verified desktop, laptop (1280px), and mobile (390px) responsiveness.

## Advanced Features (Post-MVP Roadmap)
- Multi-month trend forecasting using exponential smoothing or ARIMA.
- Automated recurring subscription detection based on transaction periodicity.
- Statement dialect detection for major Indian bank CSV formats (SBI, HDFC, ICICI).
- Encrypted SQLite database using SQLCipher for high-security environments.

## Constraints
- **Stack Requirement:** Python 3.12, Streamlit 1.66+, pandas, scikit-learn, SQLite.
- **No Cloud Services:** Zero external API keys, zero remote telemetry, 100% offline.
- **Strict Currency:** Indian Rupee (INR / ₹) with integer paise storage.
- **No Floating-Point Math:** Sums and balances must strictly compute in integer paise before decimal formatting.
- **Isolated Verification:** Tests and screenshot captures must run on an isolated port and temporary database.

## Technical Challenges
1. **Responsive Streamlit Customization:** Maintaining the high-density Dribbble Nexora look (lavender outer frame, rounded cards, sticky toolbar, quiet sidebar) without breaking layout or causing button wrapping at 1280px laptop viewports or mobile viewports.
2. **Cross-Component Navigation & Drill-Down:** Connecting client-side SVG chart interactions (e.g. pinned doughnut slices) to Streamlit server state to enable seamless 1-click filtering and page switching.
3. **Budget State Integrity:** Distinguishing between undefined budget targets ("No target") and explicit zero targets (`₹0`) without persisting default zeros or leaking drafts between months.
4. **Explainable AI Abstention:** Presenting model scores transparently without claiming calibrated probabilities, and routing low-confidence or OOV inputs to human review while respecting manual overrides.

## Chosen Technology Stack
- **Runtime:** Python 3.12.14
- **Web Interface:** Streamlit 1.66.1 with custom CSS injection and SVG chart components (`st.components.v2.component`)
- **Data Manipulation:** pandas 2.3.3
- **Machine Learning:** scikit-learn 1.9.1 (TF-IDF + LogisticRegression)
- **Database:** SQLite 3 (Python standard library `sqlite3`)
- **Testing:** pytest 9.2.0, Streamlit AppTest
- **Browser Verification:** Headless Chrome via Chrome DevTools Protocol (CDP)
