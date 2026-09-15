"""Dig into Jobs at Amazon UK SPA assets for warehouse job APIs."""
from __future__ import annotations

import re

import httpx

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Referer": "https://www.jobsatamazon.co.uk/app",
    "Origin": "https://www.jobsatamazon.co.uk",
}

client = httpx.Client(timeout=60.0, headers=HEADERS, follow_redirects=True)

html = client.get("https://www.jobsatamazon.co.uk/app").text
print("app html", len(html))
print(html[:1500])
print("---")
scripts = re.findall(r'(?:src|href)=["\']([^"\']+)["\']', html)
print("refs", scripts)

for src in scripts:
    if not any(ext in src for ext in (".js", ".css", "cloudfront")):
        continue
    url = src
    if src.startswith("/"):
        url = "https://www.jobsatamazon.co.uk" + src
    r = client.get(url)
    print("\nASSET", url, r.status_code, r.headers.get("content-type"), len(r.text))
    text = r.text
    if "ERROR" in text[:200] and "CloudFront" in text:
        print("  blocked")
        continue
    # print interesting endpoint-like strings
    urls = sorted(set(re.findall(r'https://[a-zA-Z0-9._/-]+', text)))
    interesting = [
        u
        for u in urls
        if any(k in u.lower() for k in ("api", "job", "search", "schedule", "hvh", "associate", "graphql"))
    ]
    print("  interesting urls", interesting[:40])
    for token in ["jobSearch", "getSchedule", "schedule", "/api/", "graphql", "warehouseOperative", "JobCard"]:
        if token.lower() in text.lower():
            print("  has token", token)

# Also try CloudFront career asset directly
cf = "https://d3216uwaav9lg7.cloudfront.net/assets-HVHCareer.js"
r = client.get(cf)
print("\nCF", r.status_code, len(r.text), r.headers.get("content-type"))
if r.status_code == 200 and "CloudFront" not in r.text[:200]:
    open("scripts/_hvh.js", "w", encoding="utf-8").write(r.text)
    urls = sorted(set(re.findall(r'https://[a-zA-Z0-9._/-]+', r.text)))
    interesting = [
        u
        for u in urls
        if any(k in u.lower() for k in ("api", "job", "search", "schedule", "hvh", "associate", "graphql"))
    ]
    print("cf interesting", interesting[:50])
    # path-like
    paths = sorted(set(re.findall(r'["\`](/[a-zA-Z0-9_/-]*(?:job|search|schedule|location)[a-zA-Z0-9_/-]*)["\`]', r.text)))
    print("cf paths", paths[:50])
