# Fictional data only

Created for the assignment, not downloaded from banking records or a public benchmark.

- `demo/transactions.csv`: 41 hand-designed fictional INR records, split across October (19) and November (22) 2026. Includes income, expenses and explicit transfers; every expense already has a category for a deterministic UI demo. Add a new uncategorized record to demonstrate ML inference.
- `demo/EXPECTED_TOTALS.json`: reference sums in integer paise, not rupees. Derived from the fixture and independently rechecked during setup.
- `training/categories.csv`: 72 hand-authored descriptions, 12 per class across six expense categories.
- `evaluation/categories_holdout.csv`: 18 separately authored descriptions, 3 per class. No exact description overlaps with training. These use different wording/fictional merchants but remain small, synthetic and relatively clean examples. Shared category vocabulary is intentional.

No category model has been evaluated during foundation setup. Model quality is unknown. Final evaluation must not be used for model selection. For realistic reliability claims, future work needs sufficiently varied consented/sanitized real descriptions and a new untouched evaluation set.

No source data contains credentials, real account numbers, OTPs or private financial records. Imports of personal data belong in ignored local storage, never these fixtures.
