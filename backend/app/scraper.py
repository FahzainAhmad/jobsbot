"""Scrape UK Warehouse Operative openings from jobsatamazon.co.uk."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

JOBS_AT_AMAZON_BASE = "https://www.jobsatamazon.co.uk"
SEARCH_URL = f"{JOBS_AT_AMAZON_BASE}/app#/jobSearch"
ROLE_TITLE = "Warehouse Operative"
GRAPHQL_PATH = "/graphql"


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9]+", "-", (value or "").strip())
    return cleaned.strip("-") or "role"


def _build_detail_url(job: Dict[str, Any]) -> str:
    job_id = str(job.get("jobId") or "")
    title = _slugify(job.get("jobTitle") or ROLE_TITLE)
    city = _slugify(job.get("city") or job.get("locationName") or "UK")
    return (
        f"{JOBS_AT_AMAZON_BASE}/jobDetail/en-GB/{quote(title)}/"
        f"{quote(city)}/{quote(job_id)}#/jobDetail?jobId={quote(job_id)}&locale=en-GB"
    )


def _build_apply_url(job: Dict[str, Any]) -> str:
    job_id = str(job.get("jobId") or "")
    return f"{JOBS_AT_AMAZON_BASE}/app#/jobDetail?jobId={quote(job_id)}&locale=en-GB"


def normalize_job(raw: Dict[str, Any]) -> Dict[str, Any]:
    city = (raw.get("city") or "").strip()
    state = (raw.get("state") or "").strip()
    location_name = (raw.get("locationName") or "").strip()
    location_parts = [part for part in [city, state] if part]
    location = ", ".join(location_parts) if location_parts else location_name or "United Kingdom"

    pay_min = raw.get("totalPayRateMinL10N") or raw.get("totalPayRateMin")
    pay_max = raw.get("totalPayRateMaxL10N") or raw.get("totalPayRateMax")
    if pay_min and pay_max and str(pay_min) != str(pay_max):
        pay = f"{pay_min} – {pay_max}"
    else:
        pay = str(pay_min or pay_max or "")

    schedule = (
        raw.get("employmentTypeL10N")
        or raw.get("employmentType")
        or raw.get("jobTypeL10N")
        or raw.get("jobType")
        or ""
    )
    title = (raw.get("jobTitle") or ROLE_TITLE).strip()
    short = " · ".join(part for part in [location, schedule, pay] if part)
    description = raw.get("tagLine") or (
        f"{title} role at Amazon. {short}." if short else f"{title} role at Amazon."
    )

    return {
        "id": str(raw.get("jobId") or raw.get("jobUuid") or ""),
        "title": title,
        "location": location,
        "city": city,
        "state": state,
        "country_code": "GBR",
        "company": "Amazon",
        "category": "Warehouse Operative",
        "family": raw.get("jobTypeL10N") or raw.get("jobType") or "Fulfillment",
        "business_category": "fulfillment-operations",
        "schedule": schedule,
        "posted_date": "",
        "updated_time": "",
        "pay": pay,
        "schedule_count": raw.get("scheduleCount"),
        "postal_code": raw.get("postalCode") or "",
        "description_short": short or description,
        "description": description,
        "basic_qualifications": "No previous experience required. On-the-job training provided.",
        "preferred_qualifications": "",
        "url": _build_detail_url(raw),
        "apply_url": _build_apply_url(raw),
        "is_intern": False,
        "is_manager": False,
        "locations": [],
        "featured": bool(raw.get("featuredJob")),
    }


def _is_warehouse_operative(job: Dict[str, Any]) -> bool:
    title = (job.get("jobTitle") or job.get("title") or "").strip().lower()
    # Exact UK Warehouse Operative role only (exclude Delivery Station Associate, etc.).
    return bool(re.search(r"^warehouse\s+operative\b", title))


def _build_facets(jobs: List[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    cities: Dict[str, int] = {}
    schedules: Dict[str, int] = {}
    for job in jobs:
        if job.get("city"):
            cities[job["city"]] = cities.get(job["city"], 0) + 1
        if job.get("schedule"):
            schedules[job["schedule"]] = schedules.get(job["schedule"], 0) + 1
    return {
        "categories": {ROLE_TITLE: len(jobs)} if jobs else {},
        "cities": dict(sorted(cities.items(), key=lambda x: -x[1])[:12]),
        "businesses": {"fulfillment-operations": len(jobs)} if jobs else {},
        "schedules": dict(sorted(schedules.items(), key=lambda x: -x[1])[:12]),
    }


async def _click_first(page, names: List[str]) -> bool:
    for name in names:
        locator = page.get_by_role("button", name=name)
        try:
            if await locator.count() and await locator.first.is_visible():
                await locator.first.click(timeout=2500)
                return True
        except Exception:  # noqa: BLE001
            continue
    return False


async def _dismiss_chrome(page) -> None:
    await _click_first(
        page,
        [
            "Continue without accepting",
            "Accept all",
            "Accept All",
            "I agree",
        ],
    )
    await page.wait_for_timeout(500)
    # Prefer skipping guided onboarding so we can see broader results.
    await _click_first(page, ["Close guided search", "Close", "Skip"])


async def _set_location(page, city: Optional[str]) -> None:
    query = (city or "London").strip()
    fields = page.get_by_placeholder("Enter postcode or city")
    if not await fields.count():
        return
    field = fields.first
    await field.click()
    await field.fill(query)
    await page.wait_for_timeout(1200)
    # Pick first autocomplete suggestion when available.
    options = page.locator('[role="option"]')
    if await options.count():
        await options.first.click()
    else:
        await field.press("Enter")
    await page.wait_for_timeout(800)
    await _click_first(page, ["Next", "Skip", "Show jobs", "See jobs"])


async def _expand_filters(page) -> None:
    await _click_first(page, ["View all filters", "Filters", "Filter"])
    await page.wait_for_timeout(800)
    # Widen commute if the control exists.
    for label in ["Within 100 miles", "Within 50 miles", "Nationwide", "Any"]:
        locator = page.get_by_text(label, exact=True)
        try:
            if await locator.count() and await locator.first.is_visible():
                await locator.first.click(timeout=1500)
                break
        except Exception:  # noqa: BLE001
            continue
    await _click_first(page, ["Show results", "Show jobs", "See jobs", "Apply", "Done"])


async def _fetch_via_browser(
    *,
    city: Optional[str] = None,
) -> List[Dict[str, Any]]:
    locations: List[Optional[str]]
    if city:
        locations = [city]
    else:
        locations = [
            None,
            "London",
            "Manchester",
            "Birmingham",
            "Southampton",
            "Glasgow",
            "Belfast",
            "Carlisle",
            "Exeter",
        ]

    captured: List[Dict[str, Any]] = []

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(
            headless=True,
            args=["--disable-dev-shm-usage", "--no-sandbox"],
        )
        context = await browser.new_context(
            locale="en-GB",
            geolocation={"latitude": 51.5074, "longitude": -0.1278},
            permissions=["geolocation"],
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1440, "height": 960},
        )
        page = await context.new_page()

        async def on_response(response) -> None:
            try:
                if GRAPHQL_PATH not in response.url or response.status != 200:
                    return
                payload = await response.json()
                data = (payload or {}).get("data") or {}
                block = data.get("searchJobCardsByLocation") or {}
                for card in block.get("jobCards") or []:
                    if _is_warehouse_operative(card):
                        captured.append(card)
            except Exception:  # noqa: BLE001
                return

        page.on("response", on_response)

        try:
            await page.goto(SEARCH_URL, wait_until="domcontentloaded", timeout=90000)
            await page.wait_for_timeout(3500)
            await _dismiss_chrome(page)
            await page.wait_for_timeout(2000)

            for location in locations:
                before = len(captured)
                if location:
                    await _set_location(page, location)
                    await page.wait_for_timeout(3500)
                    await _expand_filters(page)
                    await page.wait_for_timeout(2500)
                else:
                    await _click_first(page, ["Close guided search", "Skip", "Close"])
                    await page.wait_for_timeout(2500)

                logger.info(
                    "location=%s captured=%s (+%s)",
                    location or "default",
                    len(captured),
                    len(captured) - before,
                )
                # Stop early once we have a decent set.
                if len({c.get("jobId") for c in captured if c.get("jobId")}) >= 8:
                    break

        except PlaywrightTimeoutError as exc:
            raise RuntimeError(f"Timed out loading Jobs at Amazon: {exc}") from exc
        finally:
            await context.close()
            await browser.close()

    return captured


async def search_jobs(
    *,
    query: str = "",
    country: Optional[str] = None,
    city: Optional[str] = None,
    category: Optional[str] = None,
    schedule: Optional[str] = None,
    sort: str = "recent",
    offset: int = 0,
    limit: int = 24,
) -> Dict[str, Any]:
    """Search Warehouse Operative openings only."""
    del query, country, category, sort
    offset = max(0, offset)
    limit = max(1, min(limit, 100))

    raw_jobs = await _fetch_via_browser(city=city)
    normalized = [normalize_job(job) for job in raw_jobs]

    unique: List[Dict[str, Any]] = []
    seen = set()
    for job in normalized:
        key = job["id"] or f"{job['title']}|{job['location']}|{job.get('pay')}"
        if key in seen:
            continue
        seen.add(key)
        unique.append(job)

    if city:
        city_l = city.lower()
        city_filtered = [
            job
            for job in unique
            if city_l in (job.get("city") or "").lower()
            or city_l in (job.get("location") or "").lower()
            or city_l in (job.get("state") or "").lower()
        ]
        # Keep city filter only when it still yields results.
        if city_filtered:
            unique = city_filtered

    if schedule:
        schedule_l = schedule.lower()
        unique = [job for job in unique if schedule_l in (job.get("schedule") or "").lower()]

    page_jobs = unique[offset : offset + limit]
    return {
        "hits": len(unique),
        "offset": offset,
        "limit": limit,
        "query": ROLE_TITLE,
        "jobs": page_jobs,
        "source": "jobsatamazon.co.uk",
        "facets": _build_facets(page_jobs),
    }
