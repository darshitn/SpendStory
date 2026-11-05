# Student Finance Assistant — Project Specification & Discovery

## Problem
University students and young adults frequently struggle to maintain financial discipline and understand their monthly cash outflow. Existing solutions often suffer from critical issues:
1. They require live bank/UPI account linking or credentials, creating privacy and security concerns.
2. They are overly bloated with credit score tracking, loan advertisements, investments, and complex multi-currency wallets.
3. They use standard floating-point arithmetic leading to precision errors in financial accounting.
4. They rely on manual tagging for every expense, which causes tracking fatigue, or they use opaque cloud AI models that hallucinate spending categories.

Students need a fast, local, privacy-respecting financial assistant that answers three core questions:
- *Where did my recorded money go this month?*
- *Which category budgets did I exceed?*
- *What specific spending adjustments will bring me back within target?*

## Target Users
- **Primary Audience:** College students and young adults managing monthly stipends, allowances, or part-time earnings in Indian Rupees (INR).
- **Usage Environment:** Local desktop/laptop application requiring zero cloud connectivity, zero API keys, and complete data sovereignty.

## Project Goals
1. **Mathematical Accuracy:** Store and calculate all monetary quantities using integer paise (1 INR = 100 paise) to eliminate floating-point representation and rounding anomalies.
2. **Transparent AI Categorization:** Provide an explainable, local machine learning model (TF-IDF + Logistic Regression) that assists with categorizing expenses, handles vocabulary gaps with explicit abstention ("needs review"), and never overrides manual user corrections.
3. **High-Fidelity Visual Design:** Implement the exact layout, density, typography, and violet/indigo aesthetic inspired by the Dribbble "Nexora" Money Management Dashboard reference (`handoff/DRIBBBLE_UI_PROMPT.md`).
4. **Resilient Data Integrity:** Enforce atomic CSV imports, SHA-256 fingerprinting for idempotent re-imports, duplicate ID detection within uploads, safe formula-injection-resistant CSV export, and persistent SQLite storage.

## Core Features
1. **Financial Dashboard (Nexora Theme):**
   - Lavender outer frame (`#DCE2F4`) with rounded white app container (`border-radius: 24px`).
   - Narrow left navigation sidebar with thin-line icon visual hierarchy.
   - 4 equal metric cards: Recorded Income, Recorded Expenses, Recorded Surplus, Transfers Excluded.
   - Asymmetric 70/30 main chart split: Cumulative Income vs Expense trend line beside an Expense Category Doughnut chart.
   - Asymmetric 30/70 secondary chart split: Category Budgets progress bars beside a Mirrored Monthly Comparison bar chart (Income positive, Expenses negative magnitude).
2. **Transaction Management:**
   - Add income, expense, or transfer transactions with strict validation.
   - Filter transactions by month, category, and real-time search query.
   - Inline category correction and review workflow.
3. **Intelligent CSV Ingestion:**
   - File format validation (max 2 MB, 10,000 rows).
   - Atomic staging and error reporting: invalid rows block the batch, ensuring zero corrupt states.
   - Payload hashing to safely detect duplicate transactions vs conflicting ID modifications.
4. **Budgeting & Rebalancing Engine:**
   - User-configurable category budgets per month.
   - Real-time spend vs budget calculation with explicit overspend alerts.
   - Deterministic suggestions: e.g., "Reduce Food spending by ₹450.00 to stay within budget."
5. **Offline Machine Learning Categorizer:**
   - Scikit-learn Pipeline (TfidfVectorizer + LogisticRegression) trained on verified student expense descriptions.
   - Confidence thresholding and Out-Of-Vocabulary (OOV) heuristic routing uncategorized transactions to "Other (Needs Review)".
   - Dedicated evaluation tool (`scripts/evaluate_model.py`) assessing precision, recall, and Macro-F1 against an untouched holdout dataset.

## MVP Scope
- Single-user local deployment via Streamlit.
- Local SQLite database in `storage/finance.db`.
- Supported expense categories: `Food`, `Transport`, `Shopping`, `Education`, `Bills`, `Entertainment`, `Other`.
- Fixed synthetic demo dataset with exact expected totals:
  - October 2026: ₹15,000 Income, ₹9,900 Expenses, ₹5,100 Surplus (₹2,000 Transfer excluded).
  - November 2026: ₹15,000 Income, ₹8,340 Expenses, ₹6,660 Surplus (₹2,000 Transfer excluded).
- Fully interactive Dribbble Nexora UI reproduction with working navigation, month selection, transactions table, budget manager, and model evaluation metrics.

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

## Technical Challenges
1. **Streamlit Component Customization:** Streamlit's default styling is wide, utilitarian, and stark. Matching the Dribbble Nexora aesthetic (custom lavender container, subtle rounded borders, custom metric cards, exact 70/30 grid splits, custom Altair chart themes) requires surgical injected CSS and fine-tuned Altair Vega-Lite specifications without breaking responsiveness or accessibility.
2. **Idempotent Transaction Pipeline:** Distinguishing between duplicate CSV imports, row updates, and ID collisions without data loss or silent overwrites.
3. **Abstention in AI Classification:** Standard logistic regression produces calibrated pseudo-probabilities that can be deceptively high for unknown strings (e.g. out-of-vocabulary junk). The pipeline must combine confidence scores with vocabulary coverage checks to trigger human review.

## Chosen Technology Stack
- **Runtime:** Python 3.12.14
- **Web Interface:** Streamlit 1.66.1 with custom CSS injection and Altair 6.3.0
- **Data Manipulation:** pandas 2.3.3
- **Machine Learning:** scikit-learn 1.9.1 (TF-IDF + LogisticRegression)
- **Database:** SQLite 3 (Python standard library `sqlite3`)
- **Testing:** pytest 9.2.0, Streamlit AppTest
- **Browser Verification:** Headless Chromium / Edge automated screen captures
