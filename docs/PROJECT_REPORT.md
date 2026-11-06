# SpendStory — Academic Project Report

**Course:** AI for Finance (CIA-2 Assignment)  
**Submission Date:** November 6, 2026  
**Implementation Stack:** Python 3.12, Streamlit 1.66, scikit-learn 1.9, pandas 2.3, SQLite 3  
**Visual Brief:** Dribbble "Nexora" Money Management Dashboard by Atiqur Rahman / ILmix Studio  

---

## 1. Executive Summary & Problem Definition
College students and young adults frequently face fragmented cash outflows, irregular allowances, and difficulties tracking discretionary expenditure against personal budgets. Mainstream consumer finance tools suffer from privacy drawbacks (requiring direct third-party access to banking credentials/APIs), feature bloat (credit card marketing, cryptocurrency portfolios, complex multi-currency wallets), and mathematical inaccuracy stemming from floating-point arithmetic.

**SpendStory** is a local finance dashboard built to answer three fundamental questions:
1. *Where did my recorded money go this month?*
2. *Which specific category budgets did I exceed?*
3. *What actionable spending reduction will bring me back within target?*

All calculations operate in **integer paise** (1 INR = 100 paise), transfers are strictly excluded from income/expense totals, and an explainable machine learning pipeline assists with category tagging while deferring low-confidence predictions to human review.

---

## 2. System Architecture & Component Design
The system employs a strict three-tier architecture ensuring separation between presentation, business logic, and local storage:

```
+-------------------------------------------------------------------------+
|                  Presentation Layer: Streamlit 1.66                     |
|  - Nexora visual shell: pale lavender frame, rounded white surface      |
|  - 4 Summary metric cards, 70/30 trend/doughnut, 30/70 budgets/bars     |
|  - Views: Overview, Transactions, Budgets, Category Review, Model Eval  |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                  Application Logic & ML Layer (src/)                    |
|  - transactions.py: Strict RFC CSV validation, Decimal->Paise, SHA-256  |
|  - analytics.py: Integer arithmetic, budget delta suggestions, CSV safe |
|  - categorizer.py: TF-IDF + LogisticRegression + Abstention Heuristics  |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                  Persistence Layer: SQLite 3 (storage/)                 |
|  - schema: transactions table, budgets table                            |
|  - Idempotent upsert & payload fingerprint conflict prevention         |
+-------------------------------------------------------------------------+
```

---

## 3. Working Features & Visual Reproduction

The visual design is modeled on the Dribbble "Nexora" Money Management Dashboard reference:
- **Pale Lavender Canvas (`#E2E7F5`):** Outer backdrop framing a centered, rounded white application shell (`border-radius: 28px`).
- **Left sidebar** with the SpendStory wordmark, line icons, a review count, and a demo loader that skips records already present.
- **Four Financial Summary Cards:**
  - *Recorded Income:* Displays positive allowances (`₹15,000.00` in Oct, `₹19,300.00` in Nov).
  - *Recorded Expenses:* Displays spending outflow (`₹9,900.00` in Oct, `₹14,160.00` in Nov).
    - October demo expenses by category are Food ₹1,400, Transport ₹600, Shopping ₹2,000, Education ₹2,000, Bills ₹2,900, and Entertainment ₹1,000, as recorded in `data/demo/EXPECTED_TOTALS.json`.
  - *Recorded Surplus:* Truthful income minus expense delta (`₹5,100.00` in Oct, `₹5,140.00` in Nov).
  - *Transfers Excluded:* Internal account movements (`₹2,000.00` in Oct, `₹2,750.00` in Nov) isolated from budget totals.
- **Asymmetric Visualization Layout:**
  - *Top Row (70/30):* Dual cumulative income/expense trend lines with translucent fills beside an Expense Category Doughnut chart with center totals.
  - *Bottom Row (30/70):* Category budget progress tracks with overspend alerts beside a mirrored monthly comparison bar chart (income positive, expense negative magnitude).
- **Interactive Functional Views:**
  - *Transactions:* Searchable, filterable ledger with inline category editing, deletion, manual entry, and formula-injection-safe CSV export.
  - *Budgets:* Monthly budget allocation editor with automatic variance calculations and actionable reduction prompts.
  - *Category Review:* Staging queue for low-confidence model predictions allowing one-click user verification.
  - *Model Evaluation:* Live disclosure of holdout performance, sample inspection, and methodology disclosures.

---

## 4. Machine Learning Implementation & Honest Evaluation

### 4.1 Pipeline Design
- **Feature Extraction:** `TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)`
- **Classifier:** `LogisticRegression(C=1.0, max_iter=300, random_state=42)`
- **Training Set:** `data/training/categories.csv` (72 verified student descriptions across 6 categories: Food, Transport, Shopping, Education, Bills, Entertainment).
- **Abstention Mechanism:**
  1. *Out-of-Vocabulary (OOV):* If input description contains 0 recognized vocabulary n-grams, model abstains to category `Other` with `review_status = 'needs_review'`.
  2. *Confidence Thresholding:* If top softmax score < 0.25, model abstains to `Other` with `needs_review`.
  3. *User Authority:* User manual corrections override model predictions and are never overwritten during re-imports.

### 4.2 Measured Holdout Results (`data/evaluation/categories_holdout.csv`)
Evaluated strictly using `scripts/evaluate_model.py` without data contamination:
- **Holdout Samples:** 18 records
- **Overall Accuracy:** 27.8% (5 / 18 correct without manual intervention)
- **Coverage:** 27.8% (5 / 18 classified automatically)
- **Accuracy on Predictions:** 100% (5 / 5 automatically classified examples)
- **Macro-Averaged Precision:** 0.5714
- **Macro-Averaged Recall:** 0.2381
- **Macro-Averaged F1-Score:** 0.3286
- **Abstention Count:** 13 / 18 (72.2% routed safely to human review)

**Honest Scientific Appraisal:**  
The model sent 13 of the 18 synthetic examples to human review. Its five correct predictions provide limited evidence about performance on real bank statements. Arithmetic, totals, and budget suggestions use deterministic rules.

---

## 5. Visual Audit & Screenshot Reference
Real browser screenshots captured via Chrome DevTools Protocol at desktop (1440x1000) and mobile (390x844) viewports:
- Desktop Dashboard Overview: `docs/ui-implementation/desktop_dashboard.png`
- Mobile Responsive View: `docs/ui-implementation/mobile_dashboard.png`
- Transactions View: `docs/ui-implementation/transactions_view.png`
- Category Budgets View: `docs/ui-implementation/budgets_view.png`
- Category Review View: `docs/ui-implementation/category_review_view.png`
- Model Evaluation View: `docs/ui-implementation/model_evaluation_view.png`

---

## 6. Security, Integrity & Limitations
1. **Integer Arithmetic:** Zero floating-point representation bugs in currency handling.
2. **Formula Injection Defense:** CSV export sanitizes cells starting with `=`, `+`, `-`, `@`, `\t`, `\r` by prepending a single quote.
3. **Idempotency:** SHA-256 fingerprinting prevents double-counting upon re-importing identical files while rejecting conflicting ID reassignments.
4. **Current Limitations:**
   - Database is local plaintext SQLite (`storage/finance.db`); not encrypted at rest.
   - Requires manual or CSV entry; no direct bank or UPI scraping.
   - Model vocabulary is currently restricted to collegiate expenses.

---

## 7. AI-Assisted Development Disclosure
This project was developed with pair-programming assistance from Antigravity (Google DeepMind agentic assistant). Antigravity generated the modular scaffolding, Altair visualization configurations, unit test suites, and CDP headless capture scripts. Human engineering verified code behavior, corrected architectural boundaries (such as Streamlit sidebar layout separation and AppTest radio interactions), ensured statistical train/holdout isolation, and audited visual parity against the Dribbble design reference.
