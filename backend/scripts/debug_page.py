"""Debug Jobs at Amazon page structure for Warehouse Operative cards."""
from __future__ import annotations

import asyncio
from pathlib import Path

from playwright.async_api import async_playwright

OUT = Path("scripts/_debug_page")


async def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            locale="en-GB",
            geolocation={"latitude": 51.5074, "longitude": -0.1278},
            permissions=["geolocation"],
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1440, "height": 960},
        )
        page = await context.new_page()

        responses = []

        async def on_response(response):
            url = response.url
            if any(k in url for k in ("graphql", "job", "schedule", "search", "waf")):
                responses.append((response.status, url[:180]))

        page.on("response", on_response)
        await page.goto("https://www.jobsatamazon.co.uk/app#/jobSearch", wait_until="domcontentloaded", timeout=90000)
        await page.wait_for_timeout(6000)

        # Try typing a postcode into any visible input
        inputs = await page.locator("input").all()
        print("inputs", len(inputs))
        for inp in inputs[:10]:
            try:
                ph = await inp.get_attribute("placeholder")
                aria = await inp.get_attribute("aria-label")
                name = await inp.get_attribute("name")
                typ = await inp.get_attribute("type")
                print(" input", typ, name, ph, aria)
            except Exception as exc:
                print(" input err", exc)

        # Fill first text-like input with London postcode
        for inp in inputs:
            try:
                if await inp.is_visible():
                    await inp.fill("SW1A 1AA")
                    await inp.press("Enter")
                    print("filled an input")
                    break
            except Exception:
                continue

        await page.wait_for_timeout(7000)
        await page.screenshot(path=str(OUT / "search.png"), full_page=True)
        html = await page.content()
        (OUT / "search.html").write_text(html, encoding="utf-8")
        text = await page.inner_text("body")
        (OUT / "search.txt").write_text(text, encoding="utf-8")
        print("body snippet:\n", text[:2000])
        print("\nresponses:")
        for status, url in responses[:40]:
            print(status, url)

        # data-test ids
        tests = await page.eval_on_selector_all(
            "[data-test-id], [data-test-component], [data-testid]",
            "els => els.slice(0,80).map(e => ({tag:e.tagName, id:e.getAttribute('data-test-id')||e.getAttribute('data-test-component')||e.getAttribute('data-testid'), text:(e.innerText||'').slice(0,80)}))",
        )
        print("\ntest ids", len(tests))
        for item in tests[:40]:
            print(item)

        await context.close()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
