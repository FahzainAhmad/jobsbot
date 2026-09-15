# Amazon Jobsbot

Free Warehouse Operative dashboard for UK Amazon openings.

- Hosted on **GitHub Pages** (stays online with your laptop off)
- Refreshed hourly by **GitHub Actions** scraping [jobsatamazon.co.uk](https://www.jobsatamazon.co.uk)

## Live site

After the first Actions deploy:

`https://fahzainahmad.github.io/jobsbot/`

## Local API (optional)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Manual scrape export

```bash
cd backend
python scripts/export_jobs.py
```

Writes `frontend/jobs.json` used by the static dashboard.
