# Selected UI reference — Antigravity implementation prompt

Work in `D:\Projects\AI-For-Finance`.

Implement Student Finance Assistant using this specific design reference:
https://dribbble.com/shots/27090441-Money-Management-Dashboard

Full-resolution reference image:
https://cdn.dribbble.com/userupload/46750069/file/79f7bc8eb4fd80fa031eec13dabb487e.png

Reference: Money Management Dashboard by Atiqur Rahman for ILmix Studio. Use it as the visual reference for this academic project; retain attribution in project documentation. Do not claim the reference design as original work.

This is my SELECTED direction. It supersedes the four earlier generated concepts and the Editorial Ledger recommendation in docs/UI_DIRECTION.md and earlier prompts. Do not blend those themes with this one. Match this reference closely rather than inventing another generic dashboard.

## Inspect, then implement

Open and visually inspect the full-resolution image before coding. Do not rely on the title or text description. If the image cannot be accessed, report that limitation and ask for the image instead of claiming visual inspection.

Read README.md, docs/PROJECT_SPEC.md, docs/SETUP_STATUS.md and handoff/ANTIGRAVITY_PROMPT.md for the functional requirements. Inspect the current files before modifying them: if an application already exists, preserve its functioning logic and records; if only the foundation exists, implement the bounded MVP as well. This prompt controls visual design; PROJECT_SPEC.md controls financial calculations, validation and AI behavior. Ignore obsolete assumptions about implementation status in earlier setup notes when actual files show otherwise.

## Reproduce the visual structure

The source image is a 3200x2400 presentation of a desktop dashboard on a lavender background. Recreate the dashboard interface, not the black image-viewer margins or an oversized screenshot pasted into the app.

1. Very pale lavender/periwinkle outer background and a large white rounded app shell with a soft lavender outer rim/shadow. Keep the framing modest so the actual product uses the viewport efficiently. At smaller widths reduce outer margins rather than shrinking all text.
2. A narrow, full-height, pale gray left sidebar, approximately 180–210px on a 1440px desktop viewport. Small wordmark at top, thin line icons, compact navigation rows, restrained violet active state. Keep the sidebar quieter than the content.
3. A slim white top toolbar with the current view title on the left and genuinely useful actions on the right. Match the reference's compact scale and fine separators. Do not add fake notifications or a fictional signed-in profile.
4. A short greeting/overview heading and compact helper text beneath it. Avoid the huge editorial headline from earlier concepts. Put month selection, Add transaction, Import CSV and Export in compact appropriate locations, not as oversized CTA blocks.
5. Four equal summary cards across one desktop row. Pale gray surfaces, restrained rounding, small labels, dark navy tabular figures, subtle icon/menu placement only when functional. Labels: Recorded income, Recorded expenses, Recorded surplus, Transfers excluded. Do not copy the reference's unsupported Total Balance or arbitrary percentage-change text.
6. Main visualization row split roughly 70/30: broad income/expense trend panel on the left and expense-category doughnut on the right. Match the source's quiet panel surfaces, panel headings, internal padding and relative visual weight.
7. Lower visualization row split roughly 30/70: compact category-budget progress list on the left and monthly income/expense comparison on the right. Preserve this intentionally asymmetric arrangement rather than making every panel identical.
8. Keep transaction browsing and AI-category review accessible as functional views. Keep the dashboard overview visually close to the reference rather than squeezing a giant table into its main chart area.

## Visual treatment

- Match the source's light, compact, polished fintech aesthetic. Use dark navy text, muted gray labels, thin borders and understated shadows; no forest-green/ivory editorial theme.
- Published source palette includes #B2BCE2, #14182D, #993FC5, #0707AF, #373EDC, #B3B3F4 and #C7A7F0. Use the image to judge placement: pale lavender mainly outside the shell; violet/indigo and magenta mainly in charts and selected actions. Most UI surfaces remain white or very pale neutral gray.
- Use a modern sans-serif with similar density to the image, e.g. locally available Inter or a good system fallback. Typical body 13–14px, section headings 14–16px, metrics 26–32px. Retain readable contrast; do not reproduce tiny illegible presentation text.
- Use a consistent 8px spacing rhythm, approximately 20–28px main padding, 12–16px panel gaps, 12–16px panel padding and 10–14px panel radii. Tune against the reference, not arbitrary defaults.
- Use one consistent thin-line icon family, not emoji navigation. Add keyboard focus, hover, disabled, loading and validation-error states.
- No decorative 3D objects, glowing blobs, giant gradients, excessive pills, tall empty cards or unrelated marketing illustrations. The reference's violet palette is explicitly selected by me despite earlier exploration constraints.

## Charts must match the style and tell the truth

Use real interactive chart components, with hover details and consistent category colors. Native Streamlit/Altair is preferred when sufficient; a chart-specific dependency can be added locally if genuinely needed for fidelity. Do not replace real charts with screenshots or invented SVG data. Avoid automatic chart toolbars, heavy gridlines and library-default colors.

- Main trend: two smooth-looking but truthful income/expense series with subtle translucent area fills, light dashed gridlines and compact hover details. Prefer cumulative recorded income and expense within the selected month; label that explicitly and derive points from dated records. Linear interpolation is fine: do not use curves that imply fabricated intermediate values. This is not bank-balance history. For a current month, stop at the available date; do not imply future actual spending.
- Doughnut: actual expense shares with legible category legend, INR amounts in tooltips and an informative center such as total recorded expenses. Use restrained violet/magenta/blue variation as in the reference. Handle zero expenses without a fictional ring breakdown.
- Budget list: small category icons, amounts spent versus user-set budgets and slim colored progress tracks. Show an overspend label when above budget; do not hide excess behind a capped bar. No user budget means 'Set budget', not an invented allowance.
- Monthly comparison: income above the baseline and expenses below it in the reference's mirrored column composition; clearly label expenses as spending magnitudes, not refunds or negative transaction values. Tooltips show positive INR spending. Only show months represented by actual recorded data. Do not fabricate twelve months to fill the chart; our demo has October and November only.
- Avoid decorative growth percentages and fabricated tooltips. Calculate comparisons only against an available comparable period; otherwise omit them.

## Functional and stack boundaries

Retain Python 3.12, Streamlit, pandas, sklearn and SQLite. Use the existing .venv. Read version-matched Streamlit guidance in `.venv/Lib/site-packages/streamlit/.agents/skills/developing-with-streamlit/` before implementation. Scoped CSS and theme configuration are authorized to match this chosen design. Prefer stable documented selectors/native controls; do not build an entire unmaintainable HTML app inside one unsafe-markdown string. Escape user descriptions in any custom rendered HTML.

Do not migrate to React or add a separate API server just for appearance. If exact visual fidelity cannot be achieved in the existing framework, complete the closest reliable version and explain the specific remaining differences. Do not claim pixel-perfect parity without comparison.

Sidebar views: Overview, Transactions, Budgets, Category review; put model evaluation/reporting in an appropriate secondary location. Do not implement wallets, payments, goals, subscription upgrades or bank linking merely because they appear in the reference. Replace the source's Upgrade to Pro block with useful Import CSV / Load fictional demo actions. Demo loading must remain explicit and idempotent.

All visible primary controls must work: navigation, month filter, entry/import/export, budget editing and AI-category correction. No decorative search field or empty ellipsis menus. If including search, wire it to transaction search. Show a small Fictional demo data label when relevant. Category-review badges reflect actual uncertain predictions, not overspending. Keep exact paise math, transfer exclusion, CSV validation, persistence and training/holdout separation from the original specification.

## Verify visually and functionally

Run the tests and model evaluation specified in the original handoff. October demo totals must remain INR 15,000 income, INR 9,900 expenses and INR 5,100 recorded surplus, with INR 2,000 transfers excluded.

Run the app locally and inspect actual rendered output at 1440x1000, 1280x800 and approximately 390px width. At desktop, compare the sidebar, toolbar, four-card row, asymmetric chart rows, density, typography, palette and spacing with the reference. On narrow screens stack panels, adapt navigation and preserve readable controls. No clipped labels, overlapping legends or page-wide horizontal overflow.

Capture actual app screenshots to docs/ui-implementation/. Compare them with the reference and fix the most visible differences before concluding. Check empty data, loaded demo, month switching, entry/import, budget update and category correction. Verify no new browser/app errors. Screenshots must come from the real implementation, never image generation.

Finish with changed files, executed checks, observed UI flows, screenshot paths, exact startup command and remaining visual/functional gaps. Update status/docs honestly. Do not commit, push or deploy. Complete the implementation, not just a design plan.
