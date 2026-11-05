# AI Assistant Instructions & Operational Rules

## Operational Principles
1. **Financial Precision:**
   - Always calculate and store monetary values as integer paise (1 INR = 100 paise).
   - Never perform arithmetic on floating-point currencies.
   - Summing, subtracting, and comparing balances must strictly use integer arithmetic. Convert to float only at final rendering.
2. **Transfer Exclusion:**
   - Transactions with type `transfer` represent liquidity shifts between a user's own accounts (e.g., cash withdrawal or bank transfer).
   - Transfers must ALWAYS be excluded from Income, Expenses, and Recorded Surplus totals.
3. **AI Transparency & Explainability:**
   - The ML categorization engine uses scikit-learn's TF-IDF + Logistic Regression.
   - Never present class softmax scores as calibrated probabilities.
   - Out-of-vocabulary words and confidence scores below 0.40 must trigger explicit abstention ("needs review") under category `Other`.
   - Never override manual user category assignments.
   - Do not claim simple heuristics, regex patterns, or sum operations are "AI".
4. **Visual Design Integrity (Dribbble Nexora Brief):**
   - Strictly follow `handoff/DRIBBBLE_UI_PROMPT.md` and `docs/ui-reference/reference.png`.
   - Maintain the soft lavender backdrop (`#DCE2F4`) and rounded white container (`border-radius: 24px`, soft drop shadow).
   - Keep sidebar narrow and quiet (`#F7F8FA`).
   - Deliver 4 equal summary cards across one row.
   - Deliver 70/30 asymmetric trend/doughnut split and 30/70 budget/comparison split.
   - Use the violet/indigo color palette (`#373EDC`, `#993FC5`, `#B3B3F4`, `#14182D`).
   - All visible UI controls must be functional. No dummy buttons or placeholder links.
5. **Code Quality & Testing:**
   - Do not commit or push to remote Git. Use local Git commits for milestone checkpoints.
   - Inspect existing files before editing.
   - Write comprehensive pytest tests for every module.
   - Capture real browser screenshots for visual regression verification.
