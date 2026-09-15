"""Locate UK GraphQL endpoint and sample search payload for warehouse jobs."""
from __future__ import annotations

import json
import re
from pathlib import Path

import httpx

data = Path("scripts/_main.prod.js").read_text(encoding="utf-8")

# Find appsync / graphql endpoints near UK / EU
for pattern in [
    r"appsync-api\.[a-z0-9.-]+/graphql",
    r"https://[a-z0-9.-]*graphql[a-z0-9./_-]*",
    r"AtoZHVHJobSearchEU[^\"']{0,120}",
    r"execute-api[^\"']{0,160}",
    r"graphql\.amazon[^\"']{0,120}",
    r"JobSearch[^\"']{0,80}",
]:
    hits = sorted(set(re.findall(pattern, data, flags=re.I)))
    print("\nPATTERN", pattern, "->", len(hits))
    for hit in hits[:30]:
        print(" ", hit)

# Context around searchJobCardsByLocation invocation / endpoint config
idxs = [m.start() for m in re.finditer("searchJobCardsByLocation", data)]
print("\nsearchJobCardsByLocation contexts")
for i in idxs[:8]:
    snippet = re.sub(r"\s+", " ", data[max(0, i - 250) : i + 350])
    print("-", snippet[:500])
    print()

# Look for uri/url endpoint assignment
for token in ["graphqlEndpoint", "GRAPHQL_ENDPOINT", "AppSync", "appsync", "x-api-key", "apiKey", "AWSAppSync"]:
    idxs = [m.start() for m in re.finditer(token, data, flags=re.I)]
    print(token, len(idxs))
    for i in idxs[:3]:
        print(" ", re.sub(r"\s+", " ", data[max(0, i - 100) : i + 200])[:320])

# SearchScheduleRequest fields
m = re.search(r"searchScheduleRequest: SearchScheduleRequest![\s\S]{0,400}", data)
if m:
    print("\nSearchScheduleRequest nearby\n", m.group(0)[:400])

# Extract full GraphQL query string for searchJobCardsByLocation
m = re.search(
    r'query searchJobCardsByLocation\(\$searchJobRequest: SearchJobRequest!\) \{[\s\S]{0,2500}?\}"',
    data,
)
if m:
    q = m.group(0)
    print("\nFULL QUERY LEN", len(q))
    print(q[:1500])
