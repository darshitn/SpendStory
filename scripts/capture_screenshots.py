"""Capture real browser screenshots of the SpendStory application using Chrome DevTools Protocol."""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import websockets

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.storage import Database
from src.transactions import Transaction, compute_fingerprint

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
OUTPUT_DIR = Path("docs/ui-implementation")


async def cdp_command(ws, method, params=None, msg_id=1):
    payload = {"id": msg_id, "method": method, "params": params or {}}
    await ws.send(json.dumps(payload))
    while True:
        resp = await ws.recv()
        data = json.loads(resp)
        if data.get("id") == msg_id:
            return data.get("result", {})


async def take_screenshot(
    url: str,
    output_path: Path,
    width: int = 1440,
    height: int = 1000,
    hover_coords: tuple[int, int] | None = None,
    reduced_motion: bool = False,
    wait_seconds: float = 4.0,
):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Launch Chrome with remote debugging on an isolated port
    chrome_proc = subprocess.Popen(
        [
            CHROME_PATH,
            "--headless=new",
            "--remote-debugging-port=9225",
            f"--window-size={width},{height}",
            "--disable-gpu",
            "--no-first-run",
            "--no-default-browser-check",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    ws_url = None
    try:
        # Wait for CDP endpoint to become ready
        for _ in range(30):
            try:
                with urllib.request.urlopen("http://127.0.0.1:9225/json", timeout=1) as r:
                    targets = json.loads(r.read().decode())
                    for t in targets:
                        if t.get("type") == "page" and "webSocketDebuggerUrl" in t:
                            ws_url = t["webSocketDebuggerUrl"]
                            break
                    if ws_url:
                        break
            except Exception:
                await asyncio.sleep(0.3)

        if not ws_url:
            raise RuntimeError("Could not obtain Chrome WebSocket URL.")

        async with websockets.connect(ws_url) as ws:
            # Set viewport metrics
            await cdp_command(
                ws,
                "Emulation.setDeviceMetricsOverride",
                {
                    "width": width,
                    "height": height,
                    "deviceScaleFactor": 1,
                    "mobile": width < 600,
                },
                msg_id=10,
            )

            # Set reduced motion if requested
            if reduced_motion:
                await cdp_command(
                    ws,
                    "Emulation.setEmulatedMedia",
                    {"features": [{"name": "prefers-reduced-motion", "value": "reduce"}]},
                    msg_id=11,
                )

            # Navigate to Streamlit target URL
            await cdp_command(ws, "Page.navigate", {"url": url}, msg_id=12)

            # Wait until Streamlit app and content are fully mounted
            for _ in range(35):
                await asyncio.sleep(0.5)
                res = await cdp_command(
                    ws,
                    "Runtime.evaluate",
                    {
                        "expression": (
                            "Boolean(document.querySelector('.view-title') && "
                            "document.querySelectorAll('[data-testid=\"stSkeleton\"]').length === 0)"
                        )
                    },
                    msg_id=13,
                )
                ready = res.get("result", {}).get("value", False)
                if ready:
                    break

            await asyncio.sleep(wait_seconds)

            # If hover coordinates are specified, trigger mouse movement
            if hover_coords:
                hx, hy = hover_coords
                await cdp_command(
                    ws,
                    "Input.dispatchMouseEvent",
                    {"type": "mouseMoved", "x": hx, "y": hy},
                    msg_id=14,
                )
                await asyncio.sleep(0.6)

            # Capture full-quality PNG screenshot
            res = await cdp_command(ws, "Page.captureScreenshot", {"format": "png"}, msg_id=15)
            img_b64 = res.get("data", "")
            if img_b64:
                img_bytes = base64.b64decode(img_b64)
                with open(output_path, "wb") as f:
                    f.write(img_bytes)
                print(f"Captured: {output_path} ({len(img_bytes)} bytes)")
            else:
                print(f"Failed to capture data for {output_path}")

    finally:
        chrome_proc.terminate()
        chrome_proc.wait()


async def main():
    parser = argparse.ArgumentParser(description="Capture SpendStory UI screenshots")
    parser.add_argument("--port", type=int, default=int(os.environ.get("PREVIEW_PORT", "8502")))
    parser.add_argument("--db-path", type=str, default=os.environ.get("FINANCE_DB_PATH", "storage/preview_test.db"))
    args = parser.parse_args()

    port = args.port
    db_path = args.db_path
    base_url = f"http://127.0.0.1:{port}"

    print(f"Connecting to isolated preview on {base_url} using database {db_path}...")
    db = Database(db_path)

    # 1. Capture clean Overview at 1440x1000
    print("1/10: Capturing Desktop Dashboard (1440x1000)...")
    await take_screenshot(
        f"{base_url}/?nav=Overview&month=2026-10",
        OUTPUT_DIR / "desktop_dashboard.png",
        width=1440,
        height=1000,
        wait_seconds=4.0,
    )

    # 2. Capture Laptop Overview at 1280x800
    print("2/10: Capturing Laptop Dashboard (1280x800)...")
    await take_screenshot(
        f"{base_url}/?nav=Overview&month=2026-10",
        OUTPUT_DIR / "desktop_1280_dashboard.png",
        width=1280,
        height=800,
        wait_seconds=4.0,
    )

    # 3. Capture Mobile Overview at 390x844
    print("3/10: Capturing Mobile Dashboard (390x844)...")
    await take_screenshot(
        f"{base_url}/?nav=Overview&month=2026-10",
        OUTPUT_DIR / "mobile_dashboard.png",
        width=390,
        height=844,
        wait_seconds=4.0,
    )

    # 4. Capture Trend Scrubber Interaction / Hover
    print("4/10: Capturing Chart Interaction (1440x1000 with crosshair tooltip)...")
    await take_screenshot(
        f"{base_url}/?nav=Overview&month=2026-10",
        OUTPUT_DIR / "chart_interaction.png",
        width=1440,
        height=1000,
        hover_coords=(650, 310),
        wait_seconds=4.0,
    )

    # 5. Capture Transactions Ledger (1440x1000)
    print("5/10: Capturing Transactions Ledger...")
    await take_screenshot(
        f"{base_url}/?nav=Transactions&month=2026-10",
        OUTPUT_DIR / "transactions_view.png",
        width=1440,
        height=1000,
        wait_seconds=3.5,
    )

    # 6. Capture Filtered Transactions (1440x1000)
    print("6/10: Capturing Filtered Transactions...")
    await take_screenshot(
        f"{base_url}/?nav=Transactions&month=2026-10",
        OUTPUT_DIR / "transactions_filtered.png",
        width=1440,
        height=1000,
        wait_seconds=3.5,
    )

    # 7. Capture Budgets View with targets & overspend alert (1440x1000)
    print("7/10: Capturing Budgets View...")
    await take_screenshot(
        f"{base_url}/?nav=Budgets&month=2026-10",
        OUTPUT_DIR / "budgets_view.png",
        width=1440,
        height=1000,
        wait_seconds=3.5,
    )

    # 8. Capture Populated Category Review Queue (inject synthetic review items if needed)
    print("8/10: Capturing Populated Category Review Queue...")
    if not db.get_transactions(review_status="needs_review"):
        fp1 = compute_fingerprint("2026-10-18", "Campus photocopy and spiral binding", 4500, "expense")
        tx1 = Transaction(
            id="REV-TEST-001",
            date="2026-10-18",
            description="Campus photocopy and spiral binding",
            amount_paise=4500,
            type="expense",
            category="Other",
            category_source="model",
            review_status="needs_review",
            model_score=0.21,
            fingerprint=fp1,
        )
        db.add_transaction(tx1)

        fp2 = compute_fingerprint("2026-10-22", "Hostel evening snacks chai samosa", 6500, "expense")
        tx2 = Transaction(
            id="REV-TEST-002",
            date="2026-10-22",
            description="Hostel evening snacks chai samosa",
            amount_paise=6500,
            type="expense",
            category="Other",
            category_source="model",
            review_status="needs_review",
            model_score=0.23,
            fingerprint=fp2,
        )
        db.add_transaction(tx2)

    await take_screenshot(
        f"{base_url}/?nav=Category+Review&month=2026-10",
        OUTPUT_DIR / "category_review_view.png",
        width=1440,
        height=1000,
        wait_seconds=3.5,
    )

    # 8b. Capture Empty Category Review Queue (e.g. for November 2026 where all items are confirmed)
    print("8b/11: Capturing Empty Category Review Queue...")
    await take_screenshot(
        f"{base_url}/?nav=Category+Review&month=2026-11",
        OUTPUT_DIR / "category_review_empty.png",
        width=1440,
        height=1000,
        wait_seconds=3.5,
    )

    # 9. Capture Model Evaluation View
    print("9/10: Capturing Model Evaluation View...")
    await take_screenshot(
        f"{base_url}/?nav=Model+Evaluation",
        OUTPUT_DIR / "model_evaluation_view.png",
        width=1440,
        height=1000,
        wait_seconds=3.5,
    )

    # 10. Capture Reduced Motion verification session
    print("10/10: Capturing Reduced Motion session...")
    await take_screenshot(
        f"{base_url}/?nav=Overview&month=2026-10",
        OUTPUT_DIR / "reduced_motion_dashboard.png",
        width=1440,
        height=1000,
        reduced_motion=True,
        wait_seconds=3.5,
    )

    print("All screenshots successfully captured!")


if __name__ == "__main__":
    asyncio.run(main())
