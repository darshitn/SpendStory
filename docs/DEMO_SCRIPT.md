# SpendStory — Five-Minute Demo

Follow this script step-by-step during your project demonstration.

---

### Step 1: Problem Definition & Mathematical Foundation (0:00 – 0:45)
- Open the application in the browser at `http://127.0.0.1:8501`.
- Explain the student problem: fragmented spending, tracking fatigue, and risk of cloud bank linking.
- State key boundaries: Single-user, fully local, 100% offline, INR only, synthetic dataset.
- Highlight the financial integrity principle: All currency values are calculated and stored in **integer paise** (1 INR = 100 paise) to prevent binary floating-point rounding errors.

---

### Step 2: Overview and November Totals (0:45 – 1:45)
- Point out the lavender frame and the SpendStory sidebar with its category review count.
  - Four equal summary cards across one row.
- In the top toolbar, ensure **November 2026** is selected.
- Show the exact totals matching `EXPECTED_TOTALS.json`:
  - Recorded Income: **₹19,300.00**
  - Recorded Expenses: **₹14,160.00**
  - Recorded Surplus: **₹5,140.00**
  - Transfers Excluded: **₹2,750.00**
- Point to the **Transfers Excluded** metric and explain: *Transfers between own accounts (e.g., ATM withdrawals or wallet top-ups) are liquidity movements, not spending, and are strictly excluded from surplus and expense totals.*

---

### Step 3: Asymmetric Visualizations & Budget Analysis (1:45 – 2:30)
- Showcase the **Cumulative Income & Expense Trend** (70% width):
  - Truthful dual line/area progression from dated transactions (no fabricated curves).
- Showcase the **Monthly Expenses Breakdown** doughnut chart (30% width):
  - The center shows ₹14,160 in expenses across seven categories.
  - November breakdown: Food ₹3,980, Transport ₹1,170, Shopping ₹1,290, Education ₹2,150, Bills ₹3,680, Entertainment ₹900, and Other ₹990.
- Showcase the **Monthly Budgets** panel (bottom-left 30%):
  - Bills are ₹180 over target and Food has ₹220 left. Other has no target and can be reviewed in Budgets.
- Showcase the **Monthly Income vs Expenses Comparison** (bottom-right 70%):
  - Select March 2026 to show a deficit, then return to November. Mirrored columns: positive indigo income bars above baseline 0, lavender expense outflow bars below baseline 0, with positive INR spending magnitudes in hover tooltips.

---

### Step 4: AI Categorization, Review & Human-in-the-Loop Override (2:30 – 3:30)
- Navigate to **Transactions** in the sidebar.
- Click **Add New Transaction** expander.
- Enter an expense with an ambiguous/unknown description: e.g. `"Midnight campus canteen snack"`, amount `₹80.00`, category left as `(Let AI Suggest)`.
- Click **Record Transaction**:
  - Show how the offline TF-IDF + Logistic Regression model assigned `Food` or routed it to `Other (Needs Review)`.
- Navigate to **Category Review**:
  - Show the two preloaded November expenses the model left for review.
  - Demonstrate a one-click correction/confirmation (e.g. changing category to `Food`).
  - Explain: *User corrections are recorded as manual overrides in SQLite and do not silently trigger model retraining.*

---

### Step 5: Idempotency & Safe Export Demonstration (3:30 – 4:15)
- In the top toolbar, click **Export CSV** to demonstrate downloading the sanitized CSV (formula injection characters `=, +, -, @` sanitized with single quotes).
- Open **Demo tools** in the sidebar and click **Try sample data** a second time:
  - Show the notification: `0 added, 218 already present`.
  - Explain how SHA-256 fingerprinting ensures repeat imports never duplicate spending or overwrite existing user category corrections.

---

### Step 6: Model Evaluation, Limitations & Conclusion (4:15 – 5:00)
- Navigate to **Model Evaluation**:
  - Open **Explore individual examples** and compare a correct prediction with an example sent to human review.
  - Show the results from `reports/model_evaluation.json`. The model trained on 72 synthetic examples and classified 5 of 18 holdout examples (27.8% coverage). All 5 predictions were correct, and the remaining 13 examples went to review (72.2%). Overall accuracy was 5 of 18 (27.8%).
  - Explain the transparency choice: *Unrecognized merchant vocabulary safely abstains to human review rather than outputting false confidence.*
- Conclude with architecture summary: Python 3.12, Streamlit, SQLite, and scikit-learn working harmoniously in a complete, reproducible academic artifact.
