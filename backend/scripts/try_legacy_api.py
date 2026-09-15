"""Try legacy hiring.amazon API paths and Playwright feasibility."""
from __future__ import annotations

import httpx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://www.jobsatamazon.co.uk",
    "Referer": "https://www.jobsatamazon.co.uk/app",
}

urls = [
    "https://hiring.amazon.com/application/api/jobsearch/search?locale=en-GB&country=UK",
    "https://www.jobsatamazon.co.uk/application/api/jobsearch/search",
    "https://hiring.amazon.com/app#/jobSearch",
    "https://api.location.hiring.eu-west-1.hvh.a2z.com/",
    "https://api.location.hiring.eu-west-1.hvh.a2z.com/places/v1/search?q=London",
]

client = httpx.Client(timeout=30.0, headers=HEADERS, follow_redirects=True)
for url in urls:
    try:
        r = client.get(url)
        print(url, r.status_code, r.headers.get("content-type"), r.text[:180].replace("\n", " "))
    except Exception as exc:
        print(url, type(exc).__name__, exc)

# POST variants
posts = [
    (
        "https://hiring.amazon.com/application/api/jobsearch/search",
        {"locale": "en-GB", "country": "United Kingdom", "pageSize": 20},
    ),
    (
        "https://www.jobsatamazon.co.uk/application/api/jobsearch/search",
        {"locale": "en-GB", "country": "United Kingdom", "pageSize": 20},
    ),
]
for url, body in posts:
    try:
        r = client.post(url, json=body)
        print("POST", url, r.status_code, r.text[:180].replace("\n", " "))
    except Exception as exc:
        print("POST", url, type(exc).__name__, exc)
