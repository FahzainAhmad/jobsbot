"""Resolve UK GraphQL URL and auth bootstrap for jobsatamazon."""
from __future__ import annotations

import re
from pathlib import Path

data = Path("scripts/_main.prod.js").read_text(encoding="utf-8")

# Find Td function / endpoint resolver
for label, pattern in [
    ("Td def", r"Td=function\(\)\{[^}]{0,500}\}"),
    ("Td arrow", r"function Td\(\)\{[^}]{0,500}\}"),
    ("Id country", r"Id=function\(\)\{[^}]{0,300}\}"),
    ("auth lambda", r"AWS_LAMBDA.{0,200}"),
    ("authorization", r"authorization.{0,120}"),
    ("getAccessToken", r"getAccessToken.{0,160}"),
    ("unauth", r"unauth.{0,120}"),
    ("guest", r"guestToken|GuestToken|anonymous.{0,100}"),
    ("createAuth", r"createAuthLink|AUTH_TYPE.{0,160}"),
]:
    hits = re.findall(pattern, data, flags=re.I)
    print("\n==", label, len(hits))
    for hit in hits[:5]:
        print(re.sub(r"\s+", " ", hit)[:400])

# Find literal eu-west-1 appsync host ids
hosts = sorted(set(re.findall(r"https://[a-z0-9]+\.appsync-api\.eu-west-1\.amazonaws\.com/graphql", data)))
print("\nEU hosts", hosts)

# Nearby Td()
for m in re.finditer(r".{0,80}Td\(\).{0,120}", data):
    s = re.sub(r"\s+", " ", m.group(0))
    if "appsync" in s or "graphql" in s:
        print("Td call", s[:250])

# Search for hostname fragments used by Td
for frag in ["fzejimnuffbyrpqqjsgsztenym", "eu-west-1.amazonaws.com/graphql", "hvh.a2z.com"]:
    print(frag, data.count(frag))

idxs = [m.start() for m in re.finditer(r"aws_appsync_graphqlEndpoint:Td\(\)", data)]
for i in idxs[:3]:
    print("endpoint cfg", re.sub(r"\s+", " ", data[max(0, i - 300) : i + 400])[:700])
