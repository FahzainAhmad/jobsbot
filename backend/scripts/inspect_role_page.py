"""Inspect warehouse-operative role page for embedded openings."""
from __future__ import annotations

import json
import re

import httpx

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html",
}

r = httpx.get(
    "https://www.jobsatamazon.co.uk/associate-roles/warehouse-operative",
    headers=HEADERS,
    timeout=40.0,
    follow_redirects=True,
)
text = r.text
print("len", len(text))

# Extract script/json blobs
for pattern in [
    r"window\.__[A-Z_]+__\s*=\s*(\{.*?\});",
    r"<script[^>]*>([^<]*(?:jobs|schedules|openings)[^<]*)</script>",
]:
    hits = re.findall(pattern, text, flags=re.I | re.S)
    print("pattern hits", len(hits))
    for hit in hits[:5]:
        print(hit[:300])

# Print sections containing pay/location-like content
for m in re.finditer(r".{0,80}(?:£\d|From £|Southampton|Norwich|Portadown|Warehouse Operative).{0,120}", text):
    s = re.sub(r"\s+", " ", m.group(0))
    if "svg" in s or "path" in s:
        continue
    print("CTX", s[:220])

# All absolute links
links = sorted(set(re.findall(r'https?://[^\"\'\s>]+', text)))
for link in links:
    if any(k in link.lower() for k in ("job", "api", "search", "schedule", "cloudfront", "graphql")):
        print("LINK", link)

# Save for inspection
open("scripts/_warehouse_role.html", "w", encoding="utf-8").write(text)
print("saved")
