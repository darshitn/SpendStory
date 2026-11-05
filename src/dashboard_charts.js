const SVG_NS = "http://www.w3.org/2000/svg";
const INCOME = "#5149ef";
const EXPENSE = "#ce38dd";
const PALETTE = ["#cc36df", "#a651ef", "#855cf7", "#5659ef", "#3984ee", "#8aa9f5", "#6a79e2"];
const CATEGORY_COLORS = new Map(
    ["Food", "Transport", "Education", "Bills", "Shopping", "Entertainment", "Other"]
        .map((category, index) => [category, PALETTE[index]]),
);
const rupees = new Intl.NumberFormat("en-IN", {
    style: "currency", currency: "INR", maximumFractionDigits: 2, minimumFractionDigits: 0,
});
const compact = new Intl.NumberFormat("en-IN", {
    notation: "compact", maximumFractionDigits: 1,
});
let nextId = 0;

function svgNode(parent, tag, attributes = {}, content) {
    const node = document.createElementNS(SVG_NS, tag);
    for (const [attribute, value] of Object.entries(attributes)) node.setAttribute(attribute, value);
    if (content !== undefined) node.textContent = content;
    parent.append(node);
    return node;
}

function element(parent, tag, className, content) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (content !== undefined) node.textContent = content;
    parent.append(node);
    return node;
}

function makePlot(root, width, height, label) {
    const svg = svgNode(root, "svg", {
        viewBox: `0 0 ${width} ${height}`, role: "group", "aria-label": label,
    });
    return { svg, defs: svgNode(svg, "defs") };
}

function gradient(defs, id, stops, direction = {}) {
    const paint = svgNode(defs, "linearGradient", {
        id, x1: "0%", y1: "0%", x2: "0%", y2: "100%", ...direction,
    });
    stops.forEach(([offset, color, opacity]) => {
        svgNode(paint, "stop", { offset, "stop-color": color, "stop-opacity": opacity });
    });
    return `url(#${id})`;
}

function grid(svg, left, right, y, zero = false) {
    svgNode(svg, "line", { class: zero ? "zero" : "grid", x1: left, x2: right, y1: y, y2: y });
}

function axis(svg, x, y, content, anchor = "middle") {
    svgNode(svg, "text", { class: "axis", x, y, "text-anchor": anchor }, content);
}

function swatch(parent, color) {
    const dot = element(parent, "i", "swatch");
    dot.style.background = color;
    dot.setAttribute("aria-hidden", "true");
}

function chartKey(root, entries) {
    const key = element(root, "div", "chart-key");
    for (const [label, color] of entries) {
        const row = element(key, "span");
        swatch(row, color);
        row.append(document.createTextNode(label));
    }
}

function makeTooltip(root) {
    const tooltip = element(root, "div", "tip");
    tooltip.hidden = true;
    const live = element(root, "span", "chart-live");
    live.setAttribute("aria-live", "polite");
    let visibleTitle;
    return {
        show(title, entries, x, y, announce) {
            if (announce) live.textContent = [title, ...entries.map(([label, value]) => `${label} ${value}`)].join(", ");
            if (!tooltip.hidden && visibleTitle === title) return;
            visibleTitle = title;
            tooltip.replaceChildren();
            element(tooltip, "strong", "tip-title", title);
            for (const [label, value, color] of entries) {
                const row = element(tooltip, "div", "tip-row");
                const text = element(row, "span");
                swatch(text, color);
                text.append(document.createTextNode(label));
                element(row, "strong", "", value);
            }
            tooltip.hidden = false;
            const right = Math.max(4, root.clientWidth - tooltip.offsetWidth - 4);
            tooltip.style.left = `${Math.max(4, Math.min(x + 12, right))}px`;
            tooltip.style.top = `${Math.max(0, y - tooltip.offsetHeight - 12)}px`;
        },
        hide() { tooltip.hidden = true; },
    };
}

function axisStep(value) {
    if (value <= 0) return 1;
    const magnitude = 10 ** Math.floor(Math.log10(value / 4));
    const normalized = value / (4 * magnitude);
    return ([1, 2, 2.5, 5, 10].find((step) => step >= normalized) || 10) * magnitude;
}

function clampIndex(index, count) {
    return Math.min(count - 1, Math.max(0, index));
}

// One tab stop for a timeline of any length. Arrow keys move among records.
function attachTimeline(target, svg, count, indexForX, select, clear, activate, initialIndex = 0) {
    let index = initialIndex;
    let pinned = false;
    const indexForPointer = (event) => {
        const bounds = svg.getBoundingClientRect();
        return clampIndex(indexForX(event.clientX - bounds.left), count);
    };
    target.addEventListener("pointermove", (event) => {
        if (event.pointerType === "touch" || pinned) return;
        index = indexForPointer(event);
        select(index);
    });
    target.addEventListener("pointerleave", () => {
        if (!pinned && !target.matches(":focus-visible")) clear();
    });
    target.addEventListener("click", (event) => {
        const selected = indexForPointer(event);
        if (activate) {
            index = selected;
            select(index, true);
            activate(index);
            return;
        }
        pinned = !pinned || selected !== index;
        index = selected;
        if (pinned) select(index, true);
        else clear();
    });
    target.addEventListener("focus", () => {
        if (target.matches(":focus-visible")) select(index, true);
    });
    target.addEventListener("blur", () => {
        if (!pinned) clear();
    });
    target.addEventListener("keydown", (event) => {
        if (activate && (event.key === "Enter" || event.key === " ")) {
            event.preventDefault();
            activate(index);
            return;
        }
        if (event.key === "Escape") {
            pinned = false;
            clear();
            return;
        }
        const requested = { ArrowLeft: index - 1, ArrowRight: index + 1, Home: 0, End: count - 1 };
        if (!(event.key in requested)) return;
        event.preventDefault();
        index = clampIndex(requested[event.key], count);
        select(index, true);
    });
}

function renderTrend(root, rows, width, id) {
    const height = width < 450 ? 190 : 205;
    const left = 32, top = 13, right = width - 10, bottom = height - 28;
    const { svg, defs } = makePlot(root, width, height, "Cumulative income and expenses");
    const incomePaint = gradient(defs, id + "-income", [
        ["0%", "#635cf2", .39], ["65%", "#8e89ff", .15], ["100%", "#b7b2ff", .015],
    ]);
    const expensePaint = gradient(defs, id + "-expense", [
        ["0%", "#e03ddc", .39], ["70%", "#e989ed", .13], ["100%", "#f1bcf7", .015],
    ]);
    const day = ({ date }) => Date.parse(date) / 86400000;
    const first = day(rows[0]);
    const range = day(rows.at(-1)) - first;
    const x = (row) => range ? left + (right - left) * (day(row) - first) / range : (left + right) / 2;
    const maximum = Math.max(...rows.flatMap((row) => [row.income_inr, row.expense_inr]));
    const tick = axisStep(maximum);
    const upper = Math.max(tick, Math.ceil(maximum / tick) * tick);
    const y = (amount) => bottom - (bottom - top) * amount / upper;
    for (let amount = 0; amount <= upper + tick / 100; amount += tick) {
        grid(svg, left, right, y(amount), amount === 0);
        axis(svg, left - 5, y(amount) + 3, compact.format(amount), "end");
    }
    let previousGridX = -Infinity;
    for (const row of rows) {
        const position = x(row);
        if (position - previousGridX < 21) continue;
        svgNode(svg, "line", {
            class: "grid", x1: position, x2: position, y1: top, y2: bottom, opacity: .65,
        });
        previousGridX = position;
    }
    const labelCount = Math.min(rows.length, width < 470 ? 4 : 7);
    const indexes = new Set(Array.from({ length: labelCount }, (_, i) => (
        Math.round(i * (rows.length - 1) / Math.max(1, labelCount - 1))
    )));
    for (const i of indexes) {
        const row = rows[i];
        const pos = x(row);
        axis(svg, pos, bottom + 17, row.label, i === 0 ? "start" : i === rows.length - 1 ? "end" : "middle");
    }

    const clip = svgNode(defs, "clipPath", { id: id + "-trend-reveal" });
    svgNode(clip, "rect", {
        class: "reveal-x", x: left - 5, y: top - 5, width: right - left + 10, height: bottom - top + 10,
    });
    const marks = svgNode(svg, "g", { "clip-path": `url(#${id}-trend-reveal)` });
    const series = [
        ["income_inr", INCOME, incomePaint], ["expense_inr", EXPENSE, expensePaint],
    ];
    for (const [field, color, paint] of series) {
        const points = rows.map((row) => [x(row), y(row[field])]);
        const line = points.map(([px, py], i) => `${i ? "L" : "M"}${px} ${py}`).join(" ");
        if (rows.length > 1) {
            svgNode(marks, "path", {
                d: `${line} L${points.at(-1)[0]} ${bottom} L${points[0][0]} ${bottom} Z`, fill: paint,
            });
            svgNode(marks, "path", { d: line, stroke: color, "stroke-width": 2.4, fill: "none", "stroke-linejoin": "round" });
        } else {
            svgNode(marks, "circle", { cx: points[0][0], cy: points[0][1], r: 4, fill: color });
        }
    }

    const highlight = svgNode(svg, "g", { visibility: "hidden", "pointer-events": "none" });
    const band = svgNode(highlight, "rect", { y: top, height: bottom - top, width: 24, rx: 5, fill: "#b7b1ff", opacity: .22 });
    const ruler = svgNode(highlight, "line", { y1: top, y2: bottom, stroke: "#635bee", "stroke-dasharray": "3 3" });
    const dots = series.map(([, color]) => svgNode(highlight, "circle", {
        r: 4.4, fill: color, stroke: "#fff", "stroke-width": 1.7,
    }));
    const target = svgNode(svg, "rect", {
        class: "plot-target", x: left, y: top, width: right - left, height: bottom - top,
        fill: "transparent", tabindex: 0,
        "aria-label": "Inspect dated values using the left and right arrow keys",
    });
    const tooltip = makeTooltip(root);
    const positions = rows.map(x);
    const select = (i, announce) => {
        const row = rows[i];
        const position = positions[i];
        band.setAttribute("x", Math.max(left, Math.min(right - 24, position - 12)));
        ruler.setAttribute("x1", position);
        ruler.setAttribute("x2", position);
        dots.forEach((dot, j) => {
            dot.setAttribute("cx", position);
            dot.setAttribute("cy", y(row[series[j][0]]));
        });
        highlight.setAttribute("visibility", "visible");
        tooltip.show(row.label, [
            ["Income", rupees.format(row.income_inr), INCOME],
            ["Expenses", rupees.format(row.expense_inr), EXPENSE],
        ], position, Math.min(...series.map(([field]) => y(row[field]))), announce);
    };
    attachTimeline(target, svg, rows.length, (px) => (
        positions.reduce((best, current, i) => Math.abs(current - px) < Math.abs(positions[best] - px) ? i : best, 0)
    ), select, () => {
        highlight.setAttribute("visibility", "hidden");
        tooltip.hide();
    });
    chartKey(root, [["Cumulative income", INCOME], ["Cumulative expenses", EXPENSE]]);
}

function polar(cx, cy, radius, angle) {
    return [cx + radius * Math.sin(angle), cy - radius * Math.cos(angle)];
}

function renderDonut(root, rows, width, id) {
    const height = width < 220 ? 174 : 194;
    const cx = width / 2, cy = height / 2, radius = Math.min(height * .36, (width - 65) / 2);
    const { svg, defs } = makePlot(root, width, height, "Expenses by category");
    const total = rows.reduce((sum, row) => sum + row.Amount, 0);
    const circumference = Math.PI * 2 * radius;
    const mask = svgNode(defs, "mask", {
        id: id + "-donut-mask", maskUnits: "userSpaceOnUse", x: 0, y: 0, width, height,
    });
    svgNode(mask, "circle", {
        class: "reveal-ring", cx, cy, r: radius, stroke: "white", "stroke-width": 36,
        fill: "none", pathLength: 100, transform: `rotate(-90 ${cx} ${cy})`,
    });
    svgNode(svg, "circle", { cx, cy, r: radius, fill: "none", stroke: "#ebe8f8", "stroke-width": 25 });
    const ring = svgNode(svg, "g", { mask: `url(#${id}-donut-mask)` });
    let covered = 0;
    const slices = rows.map((row, i) => {
        const share = row.Amount / total;
        const color = CATEGORY_COLORS.get(row.Category) || PALETTE[i % PALETTE.length];
        const paint = gradient(defs, `${id}-slice-${i}`, [
            ["0%", color, .81], ["54%", color, 1], ["100%", color, .9],
        ], { x2: "100%" });
        const segment = svgNode(ring, "circle", {
            class: "donut-slice", cx, cy, r: radius, stroke: paint, "stroke-width": 25,
            "stroke-dasharray": `${share * circumference} ${circumference}`,
            "stroke-dashoffset": -covered * circumference, fill: "none",
            transform: `rotate(-90 ${cx} ${cy})`,
        });
        const middle = (covered + share / 2) * 2 * Math.PI;
        covered += share;
        return { row, share, color, segment, middle };
    });
    const callouts = slices.filter(({ share }) => share >= .075).map((slice) => {
        const [sx, sy] = polar(cx, cy, radius + 14, slice.middle);
        const [mx, my] = polar(cx, cy, radius + 23, slice.middle);
        return { ...slice, sx, sy, mx, my, side: mx >= cx ? 1 : -1 };
    });
    // Place labels in two independently spaced columns.
    if (width >= 165) {
        for (const side of [-1, 1]) {
            const column = callouts.filter((point) => point.side === side).sort((a, b) => a.my - b.my);
            let previous = 2;
            for (const point of column) {
                const labelY = Math.max(previous + 13, Math.min(height - 9, point.my));
                previous = labelY;
                const labelX = Math.min(width - 4, Math.max(4, point.mx + side * 7));
                svgNode(svg, "polyline", {
                    points: `${point.sx},${point.sy} ${point.mx},${labelY} ${labelX},${labelY}`,
                    fill: "none", stroke: "#bfc4d5", "stroke-width": .8, "pointer-events": "none",
                });
                svgNode(svg, "text", {
                    class: "callout", x: labelX, y: labelY - 3, "text-anchor": side === 1 ? "end" : "start",
                    "pointer-events": "none",
                }, `${Math.round(point.share * 100)}%`);
            }
        }
    }
    const value = svgNode(svg, "text", {
        class: "donut-value", x: cx, y: cy + 2, "text-anchor": "middle", "font-size": 21, "pointer-events": "none",
    });
    const caption = svgNode(svg, "text", {
        class: "donut-label", x: cx, y: cy + 20, "text-anchor": "middle", "pointer-events": "none",
    });
    const key = element(root, "div", "chart-key");
    key.setAttribute("aria-label", "Highlight an expense category");
    const buttons = slices.map(({ row, share, color }) => {
        const button = element(key, "button", "key-button");
        button.type = "button";
        button.setAttribute("aria-label", `${row.Category}, ${rupees.format(row.Amount)}, ${Math.round(share * 100)} percent`);
        swatch(button, color);
        button.append(document.createTextNode(row.Category));
        return button;
    });
    let pinned = -1;
    const highlight = (index) => {
        const selected = slices[index];
        const formatted = rupees.format(selected ? selected.row.Amount : total);
        value.textContent = formatted;
        value.setAttribute("font-size", Math.min(22, (radius * 2 - 20) / (formatted.length * .53)));
        caption.textContent = selected ? `${selected.row.Category} · ${Math.round(selected.share * 100)}%` : "Total expenses";
        slices.forEach(({ segment }, i) => {
            segment.classList.toggle("active", index === i);
            segment.classList.toggle("muted", index !== -1 && index !== i);
            buttons[i].setAttribute("aria-pressed", String(pinned === i));
        });
    };
    for (const [i, { segment }] of slices.entries()) {
        const button = buttons[i];
        const toggle = () => { pinned = pinned === i ? -1 : i; highlight(pinned); };
        for (const target of [segment, button]) {
            target.addEventListener("pointerenter", () => highlight(i));
            target.addEventListener("pointerleave", () => highlight(pinned));
            target.addEventListener("click", toggle);
        }
        button.addEventListener("focus", () => highlight(i));
        button.addEventListener("blur", () => highlight(pinned));
        button.addEventListener("keydown", (event) => {
            if (event.key === "Escape") { pinned = -1; highlight(-1); }
        });
    }
    highlight(-1);
}

function renderMonthly(root, rows, width, id, { selectedMonth, selectMonth }) {
    const height = width < 410 ? 185 : 201;
    const left = 33, right = width - 10, top = 12, bottom = height - 24;
    const baseline = (top + bottom) / 2;
    const { svg, defs } = makePlot(root, width, height, "Monthly income above and spending below zero");
    const solid = gradient(defs, id + "-bar", [
        ["0%", "#5547f3", 1], ["58%", "#382ddd", 1], ["100%", "#2a25be", 1],
    ]);
    const fade = gradient(defs, id + "-water-fade", [
        ["0%", "#fff", .88], ["62%", "#fff", .6], ["100%", "#fff", .12],
    ]);
    const pattern = svgNode(defs, "pattern", {
        id: id + "-ripples", width: 6, height: 6, patternUnits: "userSpaceOnUse",
    });
    svgNode(pattern, "path", {
        d: "M-4 4 Q-2 1 0 0 M-1 7 Q1 3 4 0 M2 8 Q4 5 8 2 M5 9 Q7 7 9 6",
        fill: "none", stroke: "#7164f1", "stroke-width": 1.15, opacity: .72,
    });
    const maxValue = Math.max(...rows.flatMap((row) => [row.income_inr, row.expense_inr]));
    const tick = axisStep(maxValue);
    const maximum = Math.max(tick, Math.ceil(maxValue / tick) * tick);
    const scale = (amount) => amount * (baseline - top) / maximum;
    for (let amount = 0; amount <= maximum + tick / 100; amount += tick) {
        grid(svg, left, right, baseline - scale(amount), amount === 0);
        axis(svg, left - 4, baseline - scale(amount) + 3, compact.format(amount), "end");
        if (amount > 0) {
            grid(svg, left, right, baseline + scale(amount));
            axis(svg, left - 4, baseline + scale(amount) + 3, `−${compact.format(amount)}`, "end");
        }
    }
    const spacing = (right - left) / rows.length;
    const barWidth = Math.min(34, Math.max(2, spacing * .56));
    const x = (index) => left + spacing * (index + .5);
    const labelsEvery = Math.max(1, Math.ceil(rows.length / Math.max(1, Math.floor((right - left) / 51))));
    const selectedIndex = rows.findIndex((row) => row.year_month === selectedMonth);
    const bandWidth = Math.min(spacing, 52);
    if (selectedIndex >= 0) {
        svgNode(svg, "rect", {
            class: "month-current", x: x(selectedIndex) - bandWidth / 2,
            y: top, width: bandWidth, height: bottom - top, rx: 6,
            fill: "#e5dfff", stroke: "#bcb1f0", "stroke-width": 1,
        });
    }
    const highlight = svgNode(svg, "rect", {
        y: top, height: bottom - top, width: bandWidth, rx: 6, fill: "#d9d4ff", opacity: .65,
        visibility: "hidden",
    });
    rows.forEach((row, i) => {
        const barX = x(i) - barWidth / 2;
        const up = scale(row.income_inr), down = scale(row.expense_inr);
        const bars = svgNode(svg, "g", {
            class: "bar", style: `--baseline: 0px ${baseline}px; --delay: ${Math.min(i * 35, 210)}ms`,
        });
        if (up > 0) svgNode(bars, "rect", {
            x: barX, y: baseline - up, width: barWidth, height: up,
            rx: Math.min(4, up / 2), fill: solid,
        });
        if (down > 0) {
            const clip = svgNode(defs, "clipPath", { id: `${id}-reflection-${i}` });
            const shape = { x: barX, y: baseline + 1, width: barWidth, height: down, rx: Math.min(3, down / 2) };
            svgNode(clip, "rect", shape);
            const mask = svgNode(defs, "mask", { id: `${id}-fade-${i}` });
            svgNode(mask, "rect", { ...shape, fill: fade });
            const reflection = svgNode(bars, "g", {
                "clip-path": `url(#${id}-reflection-${i})`, mask: `url(#${id}-fade-${i})`,
            });
            svgNode(reflection, "rect", { ...shape, fill: "#b6a9ff", opacity: .28 });
            svgNode(reflection, "rect", {
                class: "water", x: barX - 3, y: baseline + 1, width: barWidth + 6, height: down,
                fill: `url(#${id}-ripples)`,
            });
        }
        if (i % labelsEvery === 0) axis(svg, x(i), height - 8, row.month_label);
    });
    const target = svgNode(svg, "rect", {
        class: "plot-target month-target", x: left, y: top, width: right - left, height: bottom - top,
        fill: "transparent", tabindex: 0,
        "aria-label": "Explore months with the left and right arrow keys. Press Enter to open the month.",
    });
    const tooltip = makeTooltip(root);
    attachTimeline(target, svg, rows.length, (px) => Math.floor((px - left) / spacing), (i, announce) => {
        const row = rows[i];
        highlight.setAttribute("x", x(i) - bandWidth / 2);
        highlight.setAttribute("visibility", "visible");
        tooltip.show(row.month_label, [
            ["Income", rupees.format(row.income_inr), INCOME],
            ["Expenses", rupees.format(row.expense_inr), "#8977ec"],
        ], x(i), baseline - scale(row.income_inr), announce);
    }, () => {
        highlight.setAttribute("visibility", "hidden");
        tooltip.hide();
    }, (i) => {
        const month = rows[i].year_month;
        if (month !== selectedMonth) selectMonth(month);
    }, Math.max(0, selectedIndex));
    chartKey(root, [["Income ↑", INCOME], ["Expenses ↓", "#8977ec"]]);
}

export default function mountChart({ data, parentElement, setTriggerValue }) {
    const root = parentElement.querySelector(".finance-chart");
    const id = `finance-plot-${nextId++}`;
    const kind = data?.kind;
    const renderer = { trend: renderTrend, donut: renderDonut, monthly: renderMonthly }[kind];
    const rows = kind === "donut" ? data?.rows?.filter((row) => row.Amount > 0) : data?.rows;
    if (!renderer || !rows?.length) {
        root.replaceChildren();
        element(root, "p", "empty", "No recorded activity for this period.");
        return;
    }
    let renderedWidth = 0;
    const render = () => {
        const width = Math.floor(root.clientWidth);
        if (width < 60 || width === renderedWidth) return;
        renderedWidth = width;
        root.replaceChildren();
        renderer(root, rows, width, id, {
            selectedMonth: data.selectedMonth,
            selectMonth: (month) => setTriggerValue("month_selected", month),
        });
    };
    render();
    const observer = new ResizeObserver(render);
    observer.observe(root);
    return () => observer.disconnect();
}
