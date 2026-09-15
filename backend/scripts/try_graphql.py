"""Discover unauthenticated token format and try a live job search."""
from __future__ import annotations

import json
import re
from pathlib import Path

import httpx

data = Path("scripts/_main.prod.js").read_text(encoding="utf-8")

# Auth token construction snippets
for pattern in [
    r"Status\|.{0,80}",
    r"UNAUTHENTICATED\|Session\|.{0,120}",
    r"authToken[:=].{0,200}",
    r"getAuthToken.{0,250}",
    r"generateAuth.{0,250}",
    r"lambdaAuthorizer.{0,200}",
    r"Authorization.{0,180}",
]:
    hits = re.findall(pattern, data)
    print("\n==", pattern, len(hits))
    for hit in hits[:8]:
        print(re.sub(r"\s+", " ", hit)[:350])

# Extract SearchJobRequest variable construction
idxs = [m.start() for m in re.finditer("searchJobRequest", data)]
print("\nsearchJobRequest count", len(idxs))
for i in idxs[:: max(1, len(idxs)//10 )][:10]:
    print("-", re.sub(r"\s+", " ", data[max(0, i - 100) : i + 250])[:360])

GRAPHQL = "https://qy64m4juabaffl7tjakii4gdoa.appsync-api.eu-west-1.amazonaws.com/graphql"
QUERY = """
query searchJobCardsByLocation($searchJobRequest: SearchJobRequest!) {
  searchJobCardsByLocation(searchJobRequest: $searchJobRequest) {
    nextToken
    jobCards {
      jobId
      jobUuid
      jobTitle
      jobType
      employmentType
      city
      state
      postalCode
      locationName
      totalPayRateMin
      totalPayRateMax
      currencyCode
      scheduleCount
      distance
      tagLine
      featuredJob
      jobTypeL10N
      employmentTypeL10N
      totalPayRateMinL10N
      totalPayRateMaxL10N
    }
  }
}
"""

# Common UK search payload guesses
payloads = [
    {
        "locale": "en-GB",
        "country": "United Kingdom",
        "keyWords": "Warehouse Operative",
        "equalFilters": [],
        "containFilters": [],
        "rangeFilters": [],
        "orFilters": [],
        "dateFilters": [],
        "sorters": [],
        "pageSize": 20,
    },
    {
        "locale": "en-GB",
        "countryCode": "UK",
        "geoQueryLeaflet": None,
        "consolidateSchedule": True,
        "pageSize": 20,
        "jobClusterName": "Warehouse Operative",
    },
]

tokens = [
    "Status|UNAUTHENTICATED|Session|",
    "UNAUTHENTICATED",
    "Status|UNAUTHENTICATED|Session|anonymous",
]

headers_base = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0",
    "Origin": "https://www.jobsatamazon.co.uk",
    "Referer": "https://www.jobsatamazon.co.uk/app",
    "country": "UK",
}

client = httpx.Client(timeout=40.0, follow_redirects=True)

print("\n=== LIVE TRIALS ===")
for token in tokens:
    for i, variables in enumerate(payloads):
        body = {"query": QUERY, "variables": {"searchJobRequest": variables}}
        headers = {**headers_base, "Authorization": token}
        r = client.post(GRAPHQL, headers=headers, json=body)
        print("token", repr(token)[:60], "payload", i, "status", r.status_code, r.text[:220].replace("\n", " "))
