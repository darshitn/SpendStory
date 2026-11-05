# AI Assistant Instructions & Operational Rules

## Operational Principles
1. **Financial Precision:**
   - Always calculate and store monetary values as integer paise (1 INR = 100 paise).
   - Never perform arithmetic on floating-point currencies.
   - Summing, subtracting, and comparing balances must strictly use integer arithmetic. Convert to float only at final rendering.
2. **Transfer Exclusion:**
   - Transactions with type `transfer` represent liquidity shifts between a user's own accounts (e.g., cash withdrawal or savings transfer).
   - Transfers must ALWAYS be excluded from Income, Expenses, and Recorded Surplus totals.
3. **AI Transparency & Explainability:**
   - The ML categorization engine uses scikit-learn's TF-IDF + Logistic Regression.
   - Never present class softmax scores as calibrated probabilities.
   - Out-of-vocabulary words and confidence scores below threshold must trigger explicit abstention ("needs review") under category `Other`.
   - Never override manual user category assignments (`category_source="manual"`).
   - Do not claim simple heuristics, regex patterns, or sum operations are "AI".
4. **Visual Design Integrity (SpendStory Lavender Nexora Theme):**
   - Strictly follow `docs/ui-reference/reference.png` and `handoff/SPENDSTORY_FULL_UI_MEGA_PROMPT.md`.
   - Maintain the soft lavender backdrop (`linear-gradient(...)`) and rounded white container (`border-radius: 23px`, multi-layer shadow).
   - Keep sidebar narrow and quiet (`#F8FAFD`).
   - Fix all label and button wrapping at 1280px laptop viewports.
   - Ensure sticky toolbar behavior is contextual and does not show irrelevant month/search controls on Model Evaluation.
   - All visible UI controls must be functional. No dummy buttons or placeholder links.
   - Honor `prefers-reduced-motion` across all charts and UI surfaces.
5. **Testing & Evidence Isolation:**
   - Do not modify or corrupt the default production database (`storage/finance.db`).
   - Run all testing, synthetic staging, and screenshot capture in an isolated preview environment on a separate port with a temporary SQLite database (`FINANCE_DB_PATH`).
   - Write comprehensive pytest tests for every module and new feature.
   - Capture real browser screenshots for visual regression verification.
