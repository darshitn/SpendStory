"""Capture real browser screenshots of the Streamlit application using Chrome DevTools Protocol."""

from __future__ import annotations

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


async def take_screenshot(url, output_path, width=1440, height=1000, wait_seconds=5):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Launch Chrome with remote debugging
    chrome_proc = subprocess.Popen(
        [
            CHROME_PATH,
            "--headless=new",
            "--remote-debugging-port=9224",
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
        # Wait for CDP to become available
        for _ in range(25):
            try:
                with urllib.request.urlopen("http://127.0.0.1:9224/json", timeout=1) as r:
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
            # Set viewport
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

            # Navigate to Streamlit app
            await cdp_command(ws, "Page.navigate", {"url": url}, msg_id=11)

            # Wait for Streamlit page & charts to render
            await asyncio.sleep(wait_seconds)

            # Capture screenshot
            res = await cdp_command(ws, "Page.captureScreenshot", {"format": "png"}, msg_id=13)
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
    db = Database("storage/finance.db")
    # Ensure a sample unreviewed transaction exists for the Category Review screenshot
    if not db.get_transactions(review_status="needs_review"):
        fp1 = compute_fingerprint("2026-11-04", "Late night chai and samosa snack", 6000, "expense")
        tx1 = Transaction(
            id="REV-001",
            date="2026-11-04",
            description="Late night chai and samosa snack",
            amount_paise=6000,
            type="expense",
            category="Other",
            category_source="model",
            review_status="needs_review",
            model_score=0.22,
            fingerprint=fp1,
        )
        db.add_transaction(tx1)

        fp2 = compute_fingerprint("2026-11-05", "Campus xerox notes photocopy", 4000, "expense")
        tx2 = Transaction(
            id="REV-002",
            date="2026-11-05",
            description="Campus xerox notes photocopy",
            amount_paise=4000,
            type="expense",
            category="Other",
            category_source="model",
            review_status="needs_review",
            model_score=0.24,
            fingerprint=fp2,
        )
        db.add_transaction(tx2)

    base_url = "http://127.0.0.1:8501"

    print("Capturing Desktop Dashboard (1440x1000)...")
    await take_screenshot(
        f"{base_url}/?nav=Overview&month=2026-10",
        OUTPUT_DIR / "desktop_dashboard.png",
        width=1440,
        height=1000,
        wait_seconds=5,
    )

    print("Capturing Mobile Dashboard (390x844)...")
    await take_screenshot(
        f"{base_url}/?nav=Overview&month=2026-10",
        OUTPUT_DIR / "mobile_dashboard.png",
        width=390,
        height=844,
        wait_seconds=5,
    )

    print("Capturing Transactions View...")
    await take_screenshot(
        f"{base_url}/?nav=Transactions&month=2026-10",
        OUTPUT_DIR / "transactions_view.png",
        width=1440,
        height=1000,
        wait_seconds=5,
    )

    print("Capturing Budgets View...")
    await take_screenshot(
        f"{base_url}/?nav=Budgets&month=2026-10",
        OUTPUT_DIR / "budgets_view.png",
        width=1440,
        height=1000,
        wait_seconds=5,
    )

    print("Capturing Category Review View...")
    await take_screenshot(
        f"{base_url}/?nav=Category+Review&month=2026-10",
        OUTPUT_DIR / "category_review_view.png",
        width=1440,
        height=1000,
        wait_seconds=5,
    )

    print("Capturing Model Evaluation View...")
    await take_screenshot(
        f"{base_url}/?nav=Model+Evaluation",
        OUTPUT_DIR / "model_evaluation_view.png",
        width=1440,
        height=1000,
        wait_seconds=5,
    )


if __name__ == "__main__":
    asyncio.run(main())
