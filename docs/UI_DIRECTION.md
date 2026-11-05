# UI exploration — four visual directions

> Superseded for implementation: the user selected https://dribbble.com/shots/27090441-Money-Management-Dashboard as the desired reference. Follow `handoff/DRIBBBLE_UI_PROMPT.md`. The four images below are retained as earlier explorations, not the selected direction.

These images are AI-generated design concepts, not screenshots of the working project. They explore the same student-finance overview in four visual identities. The implementation specification remains authoritative for data and behavior.

## Recommended: 01 Editorial Ledger

Image: `ui-concepts/01-editorial-ledger.png`.

Warm ivory #F5F2E9 canvas, forest #173E32 navigation, near-black #222B25 text, muted brass #B49A54 accent. Serif headings and tabular financial figures, sans-serif controls, hairline dividers, minimal rounding and open numerical summary blocks. Best combination of distinctive identity and readable finance data. Size the title more modestly than the concept so actions and data have enough room at 1280px.

## 02 Cobalt Grid

Image: `ui-concepts/02-cobalt-grid.png`.

Cool white #F7F8FA, cobalt #1847DB, navy #152238, silver borders #DFE4EB. Horizontal navigation, compact grotesk type, rigid grid and restrained corners. Best for a precise productivity-oriented interface, though less distinctive than 01 or 03.

## 03 Clay & Ink

Image: `ui-concepts/03-clay-and-ink.png`.

Sand #F8F3EC, charcoal #262724, terracotta #B95336, peach #F1D8C8, olive #727B55. Asymmetric main layout and a warm budget-planning panel. A good alternative if a personal, approachable identity matters more than a formal financial-ledger feel.

## 04 Graphite & Citrus

Image: `ui-concepts/04-graphite-citrus.png`.

Graphite #191C1A, charcoal #242825, off-white #F1F3EC, sage #9BAA96, limited chartreuse #D2ED79. Restrained dark surfaces, fine separators, clear tables, no glow. For a dark interface; keep warning colors distinct from the accent.

## Implementation guidance for Antigravity

The user has explicitly requested a distinctive, polished UI rather than a default AI theme. A small scoped stylesheet is authorized if native Streamlit themes cannot achieve the chosen direction. Prefer native controls, theme configuration and charts first; avoid fragile generated CSS-class selectors, custom component infrastructure or a framework rewrite. No theme has been selected by the user yet; 01 is the recommended default if no preference is supplied.

- Use the chosen image for hierarchy, spacing, palette and typography; implement real controls rather than a screenshot as the app background.
- Keep titles, metrics, forms, navigation and tables consistent across all app views, not just Overview. Hide developer details from everyday task flows; keep model evaluation in an appropriate secondary view.
- Aim for 24–32px section gaps, 16–20px internal spacing, legible labels, aligned currency columns and subtle 1px rules. Avoid large decorative KPI boxes and repetitive nested cards.
- Use system fallbacks or locally available fonts; the app must remain usable offline. Do not make Google Fonts an essential dependency.
- Provide hover/focus/disabled/error states, keyboard-friendly native controls, mobile stacking and no horizontal overflow at common viewport widths. Keep chart labels and form text readable. Do not use color as the sole status signal.
- Validate the implemented interface at desktop and narrow widths, capture actual screenshots and distinguish visual review from passing automated tests.

## Corrections required when implementing the concepts

Generated images contain illustrative content defects. Do not copy those defects:

- Budget overspending and uncertain category prediction are separate states. 'Needs review' belongs to an uncertain transaction classification, not an over-budget category. The supplied demo CSV has confirmed categories; show no fabricated pending reviews until actual uncategorized data is added.
- Budget recommendations are deterministic calculations, not editable ML suggestions. Let users edit budgets or transaction categories; remove 'Edit suggestion' / 'Update suggestion' controls.
- Derive every chart, percentage and date from actual records. The images invent daily bars and transaction dates; those are not fixture truth. A Food budget of INR 1,200 is an illustrative example, not a supplied user budget.
- For a real spending-share chart use a consistent 0–100% denominator and display values; do not reproduce bars whose lengths imply a different scale. For budget progress over 100%, show the overspend in text without a misleading gauge.
- Local Python/Streamlit implementation details belong in About/report/evaluation, not the everyday app footer.
- Do not show the concept-number footer labels in the actual product.

All concepts were generated with the built-in image-generation tool. The accompanying prompt-set document records the requested visual specifications.
