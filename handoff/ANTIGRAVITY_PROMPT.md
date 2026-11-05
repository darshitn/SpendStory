# Antigravity implementation prompt

> UI selection update: the user chose the Dribbble Money Management Dashboard reference. Read `handoff/DRIBBBLE_UI_PROMPT.md` for the current visual direction; it supersedes prior Editorial Ledger/theme recommendations and conflicting appearance guidance below. Functional requirements remain applicable.

You are implementing my AI for Finance CIA-2 assignment in:

`D:\Projects\AI-For-Finance`

Build **Student Finance Assistant**, a working local personal finance app. Submission is November 6, 2026. Prioritize finishing the bounded MVP, explainable code and a reliable demo. Do the implementation and verification; do not stop after producing a plan.

## Read before editing

- `README.md`
- `docs/PROJECT_SPEC.md` (authoritative MVP behavior and data contract)
- `docs/REPORT_OUTLINE.md`
- `docs/DEMO_SCRIPT.md`
- `docs/SETUP_STATUS.md`
- `docs/UI_DIRECTION.md` and the four image references in `docs/ui-concepts/`. The user explicitly prioritizes excellent, distinctive UI. Follow the visual guidance and content corrections; do not copy generated-image mistakes. No theme has been selected yet; Editorial Ledger is the recommended default if no preference is supplied.
- `data/demo/transactions.csv` and `data/demo/EXPECTED_TOTALS.json`
- `data/training/categories.csv`

The initial folder contained no application. Codex prepared planning, environment and synthetic fixtures only. There is no app.py or trained model yet. Preserve these artifacts; update status accurately as work completes. Do not present foundation checks as application tests.

## Authorized implementation

Use the prepared Python 3.12 `.venv` with Streamlit, pandas, scikit-learn, pytest and stdlib SQLite. Inspect installed versions/lock file. Use version-matched Streamlit docs and standard built-in UI elements. Do not replace this stack with React, FastAPI, Docker, cloud services or Android. No API key or paid service is needed.

Version-matched Streamlit instructions and references are available locally at `.venv/Lib/site-packages/streamlit/.agents/skills/developing-with-streamlit/SKILL.md`. Read that routing file and relevant dashboard, state, caching and testing references before writing the UI. Prefer current parameters such as `width="stretch"` instead of deprecated `use_container_width`.

Allowed edits: `app.py`, `src/`, `tests/`, `scripts/`, `.streamlit/config.toml`, README, docs, dependency files and generated local files inside this project. You may add training examples to `data/training/` when justified and documented. Keep the supplied demo and held-out evaluation CSV unchanged. Do not use held-out labels to train or choose thresholds. Do not alter unrelated folders, global Python, PATH, authentication or permission settings. Do not commit, push, publish, deploy or send messages.

## Milestone 1 — working finance flow first

Create small understandable modules, for example:

- `src/transactions.py`: parsing and validation.
- `src/storage.py`: SQLite records, original import fingerprints and budgets.
- `src/analytics.py`: exact monetary totals, monthly/category summaries, budget suggestions.
- `src/categorizer.py`: training and inference.
- `app.py`: UI that calls these modules, with no database or model logic embedded in rendering functions.

Deliver manual entry, CSV preview/atomic import, explicit fictional demo loading, persistent data, month selection, totals, category chart, editable category budgets, editable transaction categories and safe CSV export. Use integer paise for storage/math and INR formatting for display. Exclude transfers from income/expenses. Do not call recorded surplus a bank balance.

Make import idempotent using IDs and original payload fingerprints. Re-importing an identical source row after a user category correction must preserve that correction and skip the source row; differing source payloads with the same ID should produce a conflict, not overwrite user work. Reject duplicate IDs inside a file before writing. Keep forms stable through Streamlit reruns, provide clear errors and require confirmation for clearing data.

Use a readable light interface, concise labels, a sidebar month selector and straightforward sections/tabs for Overview, Transactions, Budgets and Model evaluation. Prefer spacing, clear charts and useful empty states over custom CSS or decorative complexity. Keep synthetic-data and review labels visible. Do not invent user balances, model metrics or glowing product claims.

## Milestone 2 — real but modest AI

Train a TF-IDF + LogisticRegression sklearn Pipeline on the training CSV, description as input and category as target. Use a fixed seed. Fit only on training data; cache to avoid retraining each rerun. Run completely offline after package installation.

Suggest categories only for uncategorized expenses, show scores as uncalibrated model scores and route low-score or vocabulary-unknown inputs to Other/needs review. Support manual corrections without silently retraining. Preserve supplied/manual categories. Do not claim rules, sums or budget subtraction are ML.

Provide `scripts/evaluate_model.py` runnable from the project root. It must load the same actual pipeline used by the application, fit on training only, evaluate the untouched holdout, print accuracy/macro-F1/per-category results and write `reports/model_evaluation.json` with dataset counts, review counts and limitations. Report all holdout examples, including abstentions. A tiny synthetic evaluation is not proof of general banking accuracy. Do not fabricate a minimum accuracy target or hide low results. Avoid previewing holdout rows until the implementation/model settings are fixed; then report the final measurement honestly.

## Milestone 3 — verify and finish submission

Use meaningful behavioral tests: strict import validation (dates, headers, amount precision/NaN, IDs), atomic failure, repeat import, corrections surviving rerun/restart, exact October/November totals, transfer exclusion, budget math, month filters, empty data, safe export and actual model inference/unknown-input handling. Include Streamlit AppTest startup/demo smoke checks if available. Tests use temporary databases and must not touch the user's actual database.

Execute these commands (do not claim a command ran if blocked):

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/evaluate_model.py
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1 --server.headless true
```

For the final command start a temporary background process, verify localhost responds, inspect startup errors and stop only the process you started. A health response is not evidence of browser interaction; distinguish that from a manual/browser demo. If possible, actually open the local UI, exercise demo/month/category/budget/import flows and capture genuine screenshots. Never fabricate screenshots.

Independently verify supplied demo totals: October income INR 15,000, expenses INR 9,900, recorded surplus INR 5,100; November income INR 15,000, expenses INR 8,340, recorded surplus INR 6,660. Both months have INR 2,000 transfers excluded from those totals.

Complete `docs/PROJECT_REPORT.md` from the outline, approximately 2–4 pages of concise Markdown with actual evaluation results. Add `docs/VIVA_GUIDE.md` explaining each module, TF-IDF, logistic regression, train/holdout separation, why SQL/paise are used, failure cases, AI-assisted development and limitations in beginner-friendly terms. Update README and demo script to match implemented behavior. Include no invented student details. Export to other document formats only if time remains after the working MVP.

Refresh the dependency lock only if dependencies actually change. Keep local records and model binaries out of version control/submission. State SQLite is local plaintext storage unless encryption is truly implemented; do not add encryption infrastructure for this deadline.

## Boundaries and completion report

No live bank/UPI connection, Android, SMS/notifications, OCR, stock prediction, loan model, chatbot, account reconciliation, cloud deployment or financial advice. Do not expand scope because something looks impressive.

If blocked by permissions, authentication, unavailable packages or host access, report the exact blocker. Do not bypass approvals or install global tools. Resolve ordinary implementation defects yourself and continue within scope. Do not ask for routine design choices already specified.

Finish with: implemented behavior, changed files, exact checks run with results, measured model metrics, observed UI flows versus unverified flows, known limitations and exact Windows startup commands. State any incomplete acceptance criterion plainly. Also explain the project in five sentences I can use to begin my presentation.
