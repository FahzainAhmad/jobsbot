"""Try session cookie bootstrap + decode search payload builder Wu()."""
from __future__ import annotations

import re
from pathlib import Path

import httpx

data = Path("scripts/_main.prod.js").read_text(encoding="utf-8")

# Find Wu function that builds searchJobRequest
for pattern in [
    r"Wu=function\([^)]*\)\{.{0,1200}\}",
    r"function Wu\([^)]*\)\{.{0,1200}\}",
    r"Wu=\([^)]*\)=>\{.{0,1200}\}",
    r"getWafToken=.{0,500}",
    r"aws-waf-token.{0,200}",
    r"wafToken.{0,200}",
]:
    hits = re.findall(pattern, data, flags=re.S)
    print("\n==", pattern[:40], len(hits))
    for hit in hits[:3]:
        print(re.sub(r"\s+", " ", hit)[:700])

# Look for default filters related to warehouse
for token in ["Warehouse Operative", "WAREHOUSE", "FulfillmentCenter", "jobTitle", "containFilters", "equalFilters", "pin"]:
    idxs = [m.start() for m in re.finditer(re.escape(token), data)]
    print(token, len(idxs))
    for i in idxs[:2]:
        print(" ", re.sub(r"\s+", " ", data[max(0, i - 80) : i + 160])[:280])

client = httpx.Client(
    timeout=40.0,
    follow_redirects=True,
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
    },
)
r = client.get("https://www.jobsatamazon.co.uk/app")
print("\nbootstrap", r.status_code, "cookies", dict(client.cookies))

GRAPHQL = "https://qy64m4juabaffl7tjakii4gdoa.appsync-api.eu-west-1.amazonaws.com/graphql"
QUERY = """
query searchJobCardsByLocation($searchJobRequest: SearchJobRequest!) {
  searchJobCardsByLocation(searchJobRequest: $searchJobRequest) {
    nextToken
    jobCards { jobId jobTitle city state employmentType totalPayRateMinL10N locationName }
  }
}
"""
payload = {
    "query": QUERY,
    "variables": {
        "searchJobRequest": {
            "locale": "en-GB",
            "country": "United Kingdom",
            "keyWords": "",
            "equalFilters": [],
            "containFilters": [{"key": "jobTitle", "val": ["Warehouse Operative"]}],
            "rangeFilters": [],
            "orFilters": [],
            "dateFilters": [],
            "sorters": [{"fieldName": "totalPayRateMax", "ascending": "false"}],
            "pageSize": 100,
        }
    },
}
headers = {
    "Content-Type": "application/json",
    "Origin": "https://www.jobsatamazon.co.uk",
    "Referer": "https://www.jobsatamazon.co.uk/app",
    "Authorization": "Status|UNAUTHENTICATED|Session|",
    "country": "UK",
    "Accept": "application/json, text/plain, */*",
}
r2 = client.post(GRAPHQL, headers=headers, json=payload)
print("graphql", r2.status_code, r2.text[:300])
print("resp cookies", dict(client.cookies))
