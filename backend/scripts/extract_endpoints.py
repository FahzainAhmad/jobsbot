"""Extract job search endpoints from jobsatamazon main bundle."""
from __future__ import annotations

import re

import httpx

js = httpx.get(
    "https://www.jobsatamazon.co.uk/app/main.prod.js",
    timeout=60,
    headers={"User-Agent": "Mozilla/5.0"},
).text
print("len", len(js))

patterns = [
    r".{0,40}jobSearch.{0,80}",
    r".{0,40}/application/.{0,80}",
    r".{0,30}getJob.{0,60}",
    r".{0,30}searchJob.{0,60}",
    r".{0,40}/api/.{0,100}",
    r".{0,40}scheduleSearch.{0,80}",
    r".{0,40}JobCard.{0,40}",
    r"https://[^\"']+jobsatamazon[^\"']*",
    r"https://[^\"']+amazondelivers[^\"']*",
    r"https://[^\"']+hiring\.amazon[^\"']*",
]

for pattern in patterns:
    hits = re.findall(pattern, js, flags=re.I)
    uniq = []
    for hit in hits:
        cleaned = " ".join(hit.split())
        if cleaned not in uniq:
            uniq.append(cleaned)
    print("\n===", pattern)
    for hit in uniq[:15]:
        print(" ", hit[:200])

# Specific interesting tokens
for token in [
    "WIPRO",
    "workday",
    "CSOD",
    "softserve",
    "JobSearch",
    "job-search",
    "geoLocation",
    "warehouse",
    "locale=en-GB",
]:
    print(token, js.lower().count(token.lower()))
