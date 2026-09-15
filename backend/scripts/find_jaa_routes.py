"""Find concrete job search URLs inside jobsatamazon main.prod.js."""
from __future__ import annotations

import re
from pathlib import Path

import httpx

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.jobsatamazon.co.uk/app",
}

path = Path("scripts/_main.prod.js")
if not path.exists() or path.stat().st_size < 1_000_000:
    print("downloading bundle...")
    data = httpx.get(
        "https://www.jobsatamazon.co.uk/app/main.prod.js",
        headers=HEADERS,
        timeout=120.0,
        follow_redirects=True,
    ).text
    path.write_text(data, encoding="utf-8")
else:
    data = path.read_text(encoding="utf-8")

print("bundle bytes", len(data))

# Capture nearby context for key tokens
tokens = [
    "warehouseOperative",
    "jobSearch",
    "getSchedule",
    "searchSchedule",
    "scheduleSearch",
    "/api/job",
    "JobSearch",
    "consolidatedSchedules",
    "searchJobCards",
    "jobCards",
    "fetchJobs",
]
for token in tokens:
    idxs = [m.start() for m in re.finditer(re.escape(token), data)]
    print("\nTOKEN", token, "count", len(idxs))
    for i in idxs[:5]:
        snippet = data[max(0, i - 120) : i + 180]
        snippet = re.sub(r"\s+", " ", snippet)
        print(" ", snippet[:280])

# Absolute path-looking API routes
routes = sorted(
    set(
        re.findall(
            r'["\'](/[^"\']*(?:job|schedule|search|location|application)[^"\']*)["\']',
            data,
            flags=re.I,
        )
    )
)
print("\nROUTES", len(routes))
for route in routes[:80]:
    print(" ", route)

# Host + path combos
hosts = sorted(
    set(
        re.findall(
            r'https://(?:[a-z0-9.-]+\.)?(?:jobsatamazon|amazondelivers|hiring\.amazon)[a-z0-9./_-]*',
            data,
            flags=re.I,
        )
    )
)
print("\nHOSTS", len(hosts))
for host in hosts[:60]:
    print(" ", host)
