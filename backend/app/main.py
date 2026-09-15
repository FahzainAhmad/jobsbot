"""Amazon Jobs dashboard API and static UI."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .scraper import search_jobs

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"

app = FastAPI(
    title="Amazon Jobsbot",
    description="Dashboard that scrapes UK Warehouse Operative openings from jobsatamazon.co.uk",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/jobs")
async def get_jobs(
    q: str = Query("Warehouse Operative", description="Fixed to Warehouse Operative"),
    country: Optional[str] = Query("GBR", description="ISO-3 country code"),
    city: Optional[str] = Query(None),
    category: Optional[str] = Query(None, description="Ignored; role is fixed"),
    schedule: Optional[str] = Query(None, description="e.g. Full Time, Part Time"),
    sort: str = Query("recent", pattern="^(recent|relevant)$"),
    offset: int = Query(0, ge=0),
    limit: int = Query(24, ge=1, le=100),
) -> Dict[str, Any]:
    del q, country, category  # Role and market are fixed to UK Warehouse Operative.
    try:
        return await search_jobs(
            query="Warehouse Operative",
            country="GBR",
            city=city.strip() if city else None,
            schedule=schedule.strip() if schedule else None,
            sort=sort,
            offset=offset,
            limit=limit,
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"Failed to scrape Warehouse Operative jobs: {exc}") from exc


if FRONTEND_DIR.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(FRONTEND_DIR / "index.html")
