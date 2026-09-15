"""Export Warehouse Operative openings to frontend/jobs.json for GitHub Pages."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
sys.path.insert(0, str(ROOT))

from app.scraper import search_jobs  # noqa: E402


async def main() -> None:
    out = REPO / "frontend" / "jobs.json"
    previous = {}
    if out.exists():
        try:
            previous = json.loads(out.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            previous = {}

    data = await search_jobs(limit=100, offset=0)
    jobs = data.get("jobs") or []

    if not jobs and previous.get("jobs"):
        print(
            "Scrape returned 0 jobs; keeping previous feed with "
            f"{len(previous['jobs'])} openings"
        )
        return

    payload = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hits": data.get("hits", len(jobs)),
        "query": data.get("query", "Warehouse Operative"),
        "source": data.get("source", "jobsatamazon.co.uk"),
        "jobs": jobs,
        "facets": data.get("facets") or {},
    }
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(jobs)} jobs -> {out}")


if __name__ == "__main__":
    asyncio.run(main())
