# MVP specification

## Goal and boundary

Help a student answer: Where did my recorded money go this month, which budgets did I exceed, and what spending change would bring me within my targets?

Deadline: November 6, 2026. Prefer a complete, understandable local demo over extra features.

Stack: Python 3.12, Streamlit, pandas, scikit-learn and standard-library SQLite. INR only; one local user. No API keys or remote AI dependency. No authentication/deployment for this local assignment.

## Required user flow

1. Open a clean app, see an empty state and choose Load fictional demo, Import CSV, or Add transaction.
2. Preview and validate a CSV before committing it atomically. Invalid rows produce actionable errors and zero inserted rows. Reject duplicate IDs within an upload. On repeat imports skip records whose IDs and content are identical; reject conflicting reused IDs. Show inserted/skipped/rejected counts.
3. Add positive-amount income, expense or transfer entries. Persist locally in SQLite across reruns/restarts. Let users edit categories and budget amounts. Ask for confirmation before clearing locally stored records.
4. For uncategorized expenses, suggest one of six model categories. Preserve imported/manual categories. Show unreviewed predictions distinctly and allow correction. Low-scoring/unrecognized predictions go to Other with a needs-review state. A user correction does not silently retrain the model.
5. Filter by month (year and month), including a safe empty state. Show recorded income, recorded expenses, income minus expenses, category totals and category budgets. Exclude transfers from both income and expense totals. Include Other in expense totals.
6. Show deterministic suggestions with an amount, period and calculation. A category over budget by INR 600 supports 'Reduce this category by INR 600 to meet its budget'; it does not prove the user can actually save that amount. If recorded expenses exceed income, show the recorded deficit without invented recommendations.
7. Export currently filtered records. Export must protect spreadsheet formula-like descriptions beginning with =, +, -, @, tab or carriage return. Never execute CSV content or pickle files uploaded by users.

## Data contract

CSV header: `id,date,description,amount,type,category`.

- `id`: nonempty stable identifier, at most 100 characters.
- `date`: strict ISO `YYYY-MM-DD`, valid calendar date.
- `description`: nonempty text after trimming, at most 300 characters.
- `amount`: positive finite INR amount with at most two decimal places. Reject negative values, zero, NaN, infinity, malformed values and excess precision. Parse through Decimal; store integer paise and sum integer paise. Never sum binary floating-point money.
- `type`: exactly `income`, `expense` or `transfer`.
- Expense `category`: `Food`, `Transport`, `Shopping`, `Education`, `Bills`, `Entertainment`, `Other`, or empty for a suggestion. Income category is `Income`; transfer category is `Transfer` (normalize blank values for these two types).
- UTF-8 CSV, optionally BOM. Reject missing/unexpected/duplicate headers. Limit imports to 2 MB and 10,000 rows with a clear error.
- The model input is description only. Transaction IDs, labels and demo categories must not leak into features.

Additional internal fields may include category source (`imported`, `manual`, `model`), review status and model score. A score is not a calibrated probability of correctness. Store chosen budgets by year-month and category in paise.

## AI design and honest evaluation

Fit a TF-IDF + logistic regression Pipeline on `data/training/categories.csv`. Use a fixed seed and no network at inference. Make first-run training explicit, fast, repeatable and independent of Streamlit reruns. For this small dataset, caching a locally trained model is sufficient; do not require a binary artifact in the submission.

Use a provisional review threshold, documented as a heuristic; do not optimize it on the supplied final holdout. Unknown vocabulary should request review even if the classifier emits a high class score. Optional train-only cross-validation may help choose a threshold, but avoid complexity that threatens the deadline.

Report raw classifier accuracy, macro-F1 and per-category results on `data/evaluation/categories_holdout.csv`; separately report review/abstention count. Do not remove difficult cases from the denominator. The holdout is deliberately small and contains different merchant/context wording; do not promise a target accuracy or fabricate metrics. If it performs poorly, report the result and improve training coverage without copying holdout examples into training. Record that subsequent iterations after viewing holdout performance are no longer a pristine final evaluation.

Do not call category rules or budget arithmetic AI. Synthetic training and synthetic evaluation do not establish real-world reliability.

## Acceptance checks

- From a fresh environment, README commands reproduce startup, tests and evaluation.
- Demo CSV has 41 records. Expected monthly totals are in `data/demo/EXPECTED_TOTALS.json`; compute from original data independently in tests.
- Re-loading demo/re-importing identical IDs never duplicates spending; conflicting IDs fail safely.
- Import validation, exact paise math, transfer exclusion, month filtering, persistence and preservation of user category corrections have behavior tests.
- A correction survives rerun/restart, as do budget edits. Empty datasets do not crash.
- Test the real model fit/predict path, pipeline isolation from held-out labels, and safe handling of unknown descriptions; do not assert an invented accuracy target.
- UI smoke test using Streamlit AppTest if supported: startup, load demo, change month and no uncaught exception. Also run a live localhost smoke check; clearly distinguish automated checks from actual browser interaction.
- Prepare a brief report and five-minute demonstration. Include limitations and development-AI usage honestly.

## Out of scope

Bank/UPI/SMS/notification integration, Android, OCR, stock prediction, loans, financial advice chatbot, automatic transfer pairing, recurring automation, multi-currency, accounts/balance reconciliation, authentication and cloud deployment. Typed transfer records are supported; automatic recognition of transfers from raw statements is future work.
