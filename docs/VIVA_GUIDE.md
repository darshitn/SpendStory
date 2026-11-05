# Student Finance Assistant — Viva Voce Defense Guide

This guide prepares you to explain every technical decision, mathematical principle, and machine learning concept in the project during your academic viva.

---

## 1. High-Level Elevator Pitch (5 Sentences)
> "Student Finance Assistant is a privacy-first, local personal finance application designed specifically for university students managing Indian Rupee expenses. Built on Python, Streamlit, and SQLite, it eliminates floating-point rounding errors by performing all financial arithmetic in integer paise. The interface meticulously reproduces the modern Dribbble 'Nexora' Money Management Dashboard aesthetic with lavender backdrops, asymmetric visual analytics, and 100% functional controls. An offline TF-IDF and Logistic Regression pipeline provides explainable expense categorization with built-in abstention, routing unfamiliar merchant descriptions to human review rather than hallucinating wrong categories. The entire application runs offline with zero API keys, guarantees idempotent CSV imports, and protects against spreadsheet formula injection."

---

## 2. Core Architectural & Code Questions

### Q1: Why do you store and calculate money in integer paise instead of standard floats?
**Answer:**
Standard IEEE-754 binary floating-point numbers cannot accurately represent base-10 fractions like `0.1` or `0.01` (e.g., `0.1 + 0.2 = 0.30000000000000004`). In financial accounting, accumulating floating-point values causes compounding rounding errors. By converting every transaction amount at the boundary using `decimal.Decimal` to integer paise (1 INR = 100 paise), all additions, subtractions, and comparisons are exact integer operations. Division to floating-point INR is only performed at the final rendering stage.

### Q2: Why are transfers excluded from income, expenses, and surplus?
**Answer:**
A transfer (such as an ATM cash withdrawal, moving funds to a savings account, or topping up a prepaid wallet) is a liquidity shift between accounts owned by the same student. It does not represent an external inflow (allowance or earnings) or an external outflow (consumption). Counting transfers as expenses would artificially double-count spending when cash is subsequently spent on food or books.

### Q3: What is idempotent import, and how does your SHA-256 fingerprint work?
**Answer:**
Idempotency means performing an action multiple times produces the same result as performing it once. When a user imports a CSV twice:
- If a row has an existing ID and its SHA-256 fingerprint `(date, description, amount_paise, type)` matches the stored fingerprint, it is safely skipped. Any manual category corrections the user previously made are preserved.
- If a row reuses an existing ID with *different* content (e.g. changed date or amount), it is flagged as an ID conflict and rejected to prevent silent data corruption.
- If a CSV file contains duplicate IDs within itself, the entire batch is rejected atomically before writing to the database.

### Q4: How is spreadsheet formula injection prevented?
**Answer:**
When exporting to CSV, if any text cell starts with `=`, `+`, `-`, `@`, `\t`, or `\r`, spreadsheet applications like Microsoft Excel or LibreOffice Calc may interpret it as an executable formula (e.g., `=cmd|' /C calc'!A0`). In `analytics.py`, `sanitize_for_csv_cell()` prepends a single apostrophe (`'`) to any dangerous leading characters, forcing spreadsheets to treat the cell strictly as plain text.

---

## 3. Machine Learning & Categorizer Questions

### Q5: How does the AI categorization pipeline work?
**Answer:**
The pipeline uses two stages from scikit-learn:
1. `TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)`: Converts raw transaction descriptions into numerical n-gram frequency-inverse document frequency features. Sublinear term frequency scales frequencies logarithmically (`1 + log(tf)`), dampening the influence of repetitive words.
2. `LogisticRegression(C=1.0, max_iter=300, random_state=42)`: A multi-class linear classifier using softmax regression to assign class probabilities across the 6 expense categories.

### Q6: What is abstention and why is it necessary?
**Answer:**
Standard classifiers always output a class label with maximum softmax probability, even when given complete gibberish or unfamiliar merchant names. In financial systems, a false prediction misleads the student and corrupts budget tracking.
Our system implements two abstention safety nets:
1. **Vocabulary Coverage Check:** If the description has 0 overlapping tokens with the training vocabulary, the model abstains immediately.
2. **Confidence Thresholding:** If the top class score is below 0.25, the model abstains.
Abstained transactions are assigned category `Other` and flagged with `review_status = 'needs_review'`, inviting the student to confirm or correct the category.

### Q7: Why is the holdout accuracy 27.8%, and why is that honest?
**Answer:**
The training dataset contains 72 synthetic student records, while the holdout dataset contains 18 unseen descriptions with different real-world merchant names (e.g., "Harbor Diner", "Morning Roastery", "Civic Power"). Because the model has never seen those specific brand names, it properly abstains on 13 out of 18 records (72.2% abstention rate). Of the remaining 5 confident predictions, it achieves high precision. Rather than overfitting or fabricating a 95% accuracy claim, reporting the genuine 27.8% holdout accuracy accurately reflects the small dataset size and demonstrates proper scientific rigor.

### Q8: Does user category correction retrain the model automatically?
**Answer:**
No. Silently retraining a model on individual user corrections during a web session can introduce catastrophic forgetting, skew class weights, and cause unpredictable reruns. Corrections are recorded in SQLite as `category_source = 'manual'` and `review_status = 'confirmed'`, respecting user authority while keeping the ML pipeline deterministic and cached.

---

## 4. UI & Visual Engineering Questions

### Q9: How did you implement the Dribbble Nexora visual styling in Streamlit?
**Answer:**
Streamlit's default interface is plain and utilitarian. To match the Dribbble design brief:
- In `.streamlit/config.toml`, theme colors were customized with primary `#373EDC`, background `#E6EBF8`, and secondary `#F8FAFC`.
- Custom CSS injected via `st.html()` frames the app in a 28px rounded white shell with soft box shadows on a pale lavender canvas.
- The sidebar was styled into a quiet gray drawer with a custom Nexora gradient wordmark and dynamic review count badges.
- Charts were custom-engineered with Altair and Vega-Lite to produce dual smooth cumulative area lines and mirrored positive/negative monthly bars with positive INR hover tooltips.

### Q10: How did you verify the design visually?
**Answer:**
We launched the application on `http://127.0.0.1:8501` and ran an automated capture script using Chrome DevTools Protocol (CDP) over WebSockets. We captured real full-resolution screenshots at 1440x1000 (desktop) and 390x844 (mobile), compared them against the original Dribbble image, and corrected visible discrepancies (such as sidebar indentation and container padding).

---

## 5. Summary Table of Module Responsibilities

| Module | Primary Responsibility | Key Functions / Classes |
| :--- | :--- | :--- |
| `src/transactions.py` | Ingestion, strict validation, decimal conversion | `parse_amount_to_paise`, `validate_transaction_row`, `parse_transactions_csv`, `compute_fingerprint` |
| `src/storage.py` | SQLite schema, persistence, idempotent import | `Database`, `save_transactions`, `load_demo_data`, `set_budget`, `get_budgets` |
| `src/analytics.py` | Integer math, budget comparisons, safe export | `calculate_monthly_summary`, `calculate_budget_comparisons`, `calculate_cumulative_trend`, `export_transactions_to_csv` |
| `src/categorizer.py` | ML pipeline, prediction, abstention | `Categorizer`, `predict`, `get_default_categorizer` |
| `scripts/evaluate_model.py` | Standalone holdout evaluation runner | Evaluates holdout CSV, writes `reports/model_evaluation.json` |
| `scripts/capture_screenshots.py` | Automated CDP headless browser verification | Captures desktop/mobile screenshots to `docs/ui-implementation/` |
| `app.py` | Dribbble Nexora UI presentation & routing | Streamlit app layout, 4 metric cards, Altair charts, 5 navigation views |
