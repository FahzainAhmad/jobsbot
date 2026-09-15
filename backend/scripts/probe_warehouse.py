"""Probe Amazon warehouse operative job sources."""
from __future__ import annotations

import json
import re
from typing import Any

import httpx

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
}


def main() -> None:
    client = httpx.Client(timeout=40.0, headers=HEADERS, follow_redirects=True)

    pages = [
        "https://www.jobsatamazon.co.uk/app",
        "https://www.jobsatamazon.co.uk/",
        "https://www.jobsatamazon.co.uk/associate-roles/warehouse-operative",
    ]
    for url in pages:
        try:
            r = client.get(url)
            print("PAGE", url, r.status_code, r.headers.get("content-type"), len(r.text))
            scripts = re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', r.text)
            print("  scripts", scripts[:12])
            for hint in ["api", "graphql", "jobSearch", "schedule", "CSOD", "salesforce"]:
                if hint.lower() in r.text.lower():
                    print("  contains", hint)
        except Exception as exc:  # noqa: BLE001
            print("PAGE ERR", url, exc)

    # Fetch main JS bundles if present and look for endpoints
    r = client.get("https://www.jobsatamazon.co.uk/app")
    scripts = re.findall(r'src=["\']([^"\']+\.js[^"\']*)["\']', r.text)
    endpoint_hits = []
    for src in scripts[:15]:
        if src.startswith("/"):
            src = "https://www.jobsatamazon.co.uk" + src
        elif src.startswith("./"):
            src = "https://www.jobsatamazon.co.uk/app/" + src[2:]
        try:
            js = client.get(src).text
        except Exception:
            continue
        found = set(
            re.findall(
                r'https?://[a-zA-Z0-9._/-]*(?:job|search|schedule|hiring|associate)[a-zA-Z0-9._/-]*',
                js,
                flags=re.I,
            )
        )
        found |= set(re.findall(r'["\'](/[^"\']*(?:job|search|schedule)[^"\']*)["\']', js, flags=re.I))
        if found:
            print("JS", src, "->", list(found)[:20])
            endpoint_hits.extend(found)

    # Try amazon.jobs with filters that might catch SF warehouse operative
    print("\n=== amazon.jobs probes ===")
    probes = [
        {"base_query": "Warehouse Operative", "country": "GBR", "result_limit": 50, "sort": "relevant"},
        {"base_query": "\"Warehouse Operative\"", "result_limit": 50, "sort": "relevant"},
        {"base_query": "SF warehouse", "country": "GBR", "result_limit": 20, "sort": "recent"},
        {
            "category[]": "fulfillment-center-warehouse-associate",
            "result_limit": 50,
            "sort": "recent",
            "offset": 0,
        },
        {"base_query": "FC Associate", "country": "GBR", "result_limit": 20, "sort": "recent"},
        {"base_query": "Sort Centre", "country": "GBR", "result_limit": 20, "sort": "recent"},
    ]
    for params in probes:
        r = client.get(
            "https://www.amazon.jobs/en/search.json",
            params=params,
            headers={**HEADERS, "Accept": "application/json", "Referer": "https://www.amazon.jobs/en/"},
        )
        data = r.json()
        jobs = data.get("jobs") or []
        print("PROBES", params, "hits", data.get("hits"))
        for job in jobs[:8]:
            title = job.get("title") or ""
            if any(k in title.lower() for k in ("warehouse", "operative", "associate", "sort", "fulfilment")):
                print(" *", title, "|", job.get("job_path"), "|", job.get("location"))

    # Try jobsatamazon common APIs
    print("\n=== jobsatamazon API guesses ===")
    guesses = [
        "https://www.jobsatamazon.co.uk/api/jobs",
        "https://www.jobsatamazon.co.uk/api/jobSearch",
        "https://www.jobsatamazon.co.uk/app/api/jobs",
        "https://www.jobsatamazon.co.uk/services/search",
        "https://hiring.amazon.com/app#/jobSearch",
        "https://autosearch.jobsatamazon.co.uk/search",
    ]
    for url in guesses:
        try:
            r = client.get(url, headers={**HEADERS, "Accept": "application/json"})
            print(url, r.status_code, (r.headers.get("content-type") or "")[:40], r.text[:160].replace("\n", " "))
        except Exception as exc:  # noqa: BLE001
            print(url, type(exc).__name__, exc)


if __name__ == "__main__":
    main()
