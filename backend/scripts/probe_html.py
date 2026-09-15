"""Probe public HTML / SEO surfaces for Warehouse Operative listings."""
from __future__ import annotations

import re

import httpx

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/json",
}

urls = [
    "https://www.jobsatamazon.co.uk/associate-roles/warehouse-operative",
    "https://www.jobsatamazon.co.uk/app#/jobSearch",
    "https://www.jobsatamazon.co.uk/search?role=Warehouse%20Operative",
    "https://www.jobsatamazon.co.uk/jobsearch",
    "https://www.jobsatamazon.co.uk/sitemap.xml",
    "https://www.jobsatamazon.co.uk/robots.txt",
    "https://www.amazon.jobs/en-gb/search.json?base_query=Warehouse%20Operative&result_limit=20&sort=recent",
    "https://www.amazon.jobs/en/search.json?base_query=SF&country=GBR&result_limit=20&sort=recent",
    "https://www.amazon.jobs/en/search.json?base_query=warehouse&job_category=Fulfillment%20Associate&country=GBR&result_limit=20",
    "https://hiring.amazon.co.uk/",
    "https://www.amazondelivers.jobs/",
]

client = httpx.Client(timeout=40.0, headers=HEADERS, follow_redirects=True)
for url in urls:
    try:
        r = client.get(url)
        ctype = r.headers.get("content-type", "")
        text = r.text
        print("\nURL", url)
        print(" ", r.status_code, ctype, "len", len(text), "final", r.url)
        if "json" in ctype:
            try:
                data = r.json()
                print("  hits", data.get("hits"), "jobs", len(data.get("jobs") or []))
                for j in (data.get("jobs") or [])[:5]:
                    print("   -", j.get("title"), "|", j.get("job_path"), "|", j.get("location"))
            except Exception as exc:
                print("  json err", exc, text[:160])
        else:
            # Find job detail links / titles
            links = re.findall(r'href=["\']([^"\']*jobDetail[^"\']*)["\']', text, flags=re.I)
            links += re.findall(r'href=["\']([^"\']*Warehouse-Operative[^"\']*)["\']', text, flags=re.I)
            titles = re.findall(r"Warehouse Operative", text)
            print("  warehouse mentions", len(titles), "jobDetail links", len(set(links)))
            for link in list(dict.fromkeys(links))[:8]:
                print("   link", link[:160])
            # JSON-LD?
            ld = re.findall(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', text, flags=re.I | re.S)
            print("  ld+json blocks", len(ld))
            for block in ld[:2]:
                print("   ", block[:220].replace("\n", " "))
    except Exception as exc:
        print("\nURL", url, "ERR", type(exc).__name__, exc)
