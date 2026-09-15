"""Debug proper location flow + /graphql interception."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from playwright.async_api import async_playwright

OUT = Path("scripts/_debug_page")


async def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    payloads = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            locale="en-GB",
            geolocation={"latitude": 53.4808, "longitude": -2.2426},  # Manchester
            permissions=["geolocation"],
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1440, "height": 960},
        )
        page = await context.new_page()

        async def on_response(response):
            if "/graphql" not in response.url:
                return
            try:
                data = await response.json()
            except Exception:
                return
            payloads.append({"status": response.status, "url": response.url, "data": data})

        page.on("response", on_response)

        await page.goto("https://www.jobsatamazon.co.uk/app#/jobSearch", wait_until="domcontentloaded", timeout=90000)
        await page.wait_for_timeout(3000)

        # Cookie banner
        for text in ["Continue without accepting", "Accept all", "Accept All"]:
            btn = page.get_by_role("button", name=text)
            if await btn.count():
                try:
                    await btn.first.click(timeout=2000)
                    print("clicked", text)
                except Exception:
                    pass

        await page.wait_for_timeout(1000)

        # Close guided search if present
        for text in ["Close guided search", "Close"]:
            btn = page.get_by_role("button", name=text)
            if await btn.count():
                try:
                    await btn.first.click(timeout=2000)
                    print("clicked", text)
                except Exception:
                    pass

        await page.wait_for_timeout(1000)

        # Fill postcode field specifically
        loc = page.get_by_placeholder("Enter postcode or city")
        print("location fields", await loc.count())
        if await loc.count():
            await loc.first.click()
            await loc.first.fill("M1 1AE")
            await page.wait_for_timeout(1500)
            # Choose suggestion if any
            suggestion = page.locator('[role="option"], li, button').filter(has_text="Manchester")
            if await suggestion.count():
                await suggestion.first.click()
                print("picked Manchester suggestion")
            else:
                await loc.first.press("Enter")
                print("pressed enter on location")

        # Next on guided search
        nxt = page.get_by_role("button", name="Next")
        if await nxt.count():
            try:
                await nxt.first.click(timeout=2000)
                print("clicked Next")
            except Exception:
                pass

        await page.wait_for_timeout(5000)

        # Try View all filters + Warehouse Operative
        for text in ["View all filters", "Filters", "Job role"]:
            btn = page.get_by_role("button", name=text)
            if await btn.count():
                try:
                    await btn.first.click(timeout=2000)
                    print("clicked", text)
                except Exception:
                    pass

        await page.wait_for_timeout(1000)
        role = page.get_by_text("Warehouse Operative", exact=True)
        print("warehouse exact matches", await role.count())
        if await role.count():
            try:
                await role.nth(min(1, await role.count() - 1)).click(timeout=2000)
                print("clicked warehouse operative text")
            except Exception as exc:
                print("role click failed", exc)

        await page.wait_for_timeout(6000)
        await page.screenshot(path=str(OUT / "after_location.png"), full_page=True)
        text = await page.inner_text("body")
        (OUT / "after_location.txt").write_text(text, encoding="utf-8")
        print("body:\n", text[:2500])

        print("\ngraphql payloads", len(payloads))
        (OUT / "graphql.json").write_text(json.dumps(payloads, indent=2)[:200000], encoding="utf-8")
        for i, payload in enumerate(payloads):
            data = payload["data"]
            keys = list((data.get("data") or {}).keys()) if isinstance(data, dict) else []
            print(i, payload["status"], keys, str(data)[:180].replace("\n", " "))

        await context.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
