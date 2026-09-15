"""Quick smoke test for Warehouse Operative scraper."""
from __future__ import annotations

import asyncio
import json

from app.scraper import search_jobs


async def main() -> None:
    data = await search_jobs(limit=10, offset=0)
    print("hits", data.get("hits"))
    print("source", data.get("source"))
    print("n", len(data.get("jobs") or []))
    for job in data.get("jobs") or []:
        print("-", job.get("title"), "|", job.get("location"), "|", job.get("pay"), "|", job.get("schedule"), "|", job.get("id"))
    print(json.dumps(data.get("facets"), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
