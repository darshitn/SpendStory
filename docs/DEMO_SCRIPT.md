# Five-Minute Presentation & Demo Script

Follow this script step-by-step during your project demonstration.

---

### Step 1: Problem Definition & Mathematical Foundation (0:00 – 0:45)
- Open the application in the browser at `http://127.0.0.1:8501`.
- Explain the student problem: fragmented spending, tracking fatigue, and risk of cloud bank linking.
- State key boundaries: Single-user, fully local, 100% offline, INR only, synthetic dataset.
- Highlight the financial integrity principle: All currency values are calculated and stored in **integer paise** (1 INR = 100 paise) to prevent binary floating-point rounding errors.

---

### Step 2: Dribbble Nexora UI Walkthrough & October Totals (0:45 – 1:45)
- Point out the visual fidelity to the Dribbble "Nexora" Money Management Dashboard brief:
  - Pale lavender backdrop (`#E2E7F5`), 28px rounded white application shell.
  - Quiet pale-gray sidebar with Nexora wordmark and dynamic review badges.
  - Four equal summary cards across one row.
- In the top toolbar, ensure **October 2026** is selected.
- Show the exact totals matching `EXPECTED_TOTALS.json`:
  - Recorded Income: **₹15,000.00**
  - Recorded Expenses: **₹9,900.00**
  - Recorded Surplus: **₹5,100.00**
  - Transfers Excluded: **₹2,000.00**
- Point to the **Transfers Excluded** metric and explain: *Transfers between own accounts (e.g., ATM withdrawals or wallet top-ups) are liquidity movements, not spending, and are strictly excluded from surplus and expense totals.*

---

### Step 3: Asymmetric Visualizations & Budget Analysis (1:45 – 2:30)
- Showcase the **Cumulative Income & Expense Trend** (70% width):
  - Truthful dual line/area progression from dated transactions (no fabricated curves).
- Showcase the **Monthly Expenses Breakdown** doughnut chart (30% width):
  - Category shares with centered ₹9,900.00 total expense label.
- Showcase the **Monthly Budgets** panel (bottom-left 30%):
  - Progress bars against targets and deterministic suggestions.
- Showcase the **Monthly Income vs Expenses Comparison** (bottom-right 70%):
  - Mirrored columns: positive indigo income bars above baseline 0, lavender expense outflow bars below baseline 0, with positive INR spending magnitudes in hover tooltips.

---

### Step 4: AI Categorization, Review & Human-in-the-Loop Override (2:30 – 3:30)
- Navigate to **Transactions** in the sidebar.
- Click **Add New Transaction** expander.
- Enter an expense with an ambiguous/unknown description: e.g. `"Midnight campus canteen snack"`, amount `₹80.00`, category left as `(Let AI Suggest)`.
- Click **Record Transaction**:
  - Show how the offline TF-IDF + Logistic Regression model assigned `Food` or routed it to `Other (Needs Review)`.
- Navigate to **Category Review**:
  - Show the staging queue of transactions needing review with model confidence scores.
  - Demonstrate a one-click correction/confirmation (e.g. changing category to `Food`).
  - Explain: *User corrections are recorded as manual overrides in SQLite and do not silently trigger model retraining.*

---

### Step 5: Idempotency & Safe Export Demonstration (3:30 – 4:15)
- In the top toolbar, click **Export CSV** to demonstrate downloading the sanitized CSV (formula injection characters `=, +, -, @` sanitized with single quotes).
- In the sidebar, click **Load Fictional Demo** a second time:
  - Show the notification: `Inserted: 0, Skipped: 41`.
  - Explain how SHA-256 fingerprinting ensures repeat imports never duplicate spending or overwrite existing user category corrections.

---

### Step 6: Model Evaluation, Limitations & Conclusion (4:15 – 5:00)
- Navigate to **Model Evaluation**:
  - Show genuine holdout results from `reports/model_evaluation.json`: 72 training records, 18 holdout records, 27.8% raw accuracy, 72.2% abstention rate.
  - Explain the transparency choice: *Unrecognized merchant vocabulary safely abstains to human review rather than outputting false confidence.*
- Conclude with architecture summary: Python 3.12, Streamlit, SQLite, and scikit-learn working harmoniously in a complete, reproducible academic artifact.
