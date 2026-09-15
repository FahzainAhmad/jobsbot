const state = {
  offset: 0,
  limit: 24,
  hits: 0,
  jobs: [],
  allJobs: [],
  selectedId: null,
  loading: false,
  mode: "static",
  updatedAt: null,
};

const els = {
  form: document.getElementById("searchForm"),
  city: document.getElementById("city"),
  schedule: document.getElementById("schedule"),
  jobList: document.getElementById("jobList"),
  statusLine: document.getElementById("statusLine"),
  lastUpdated: document.getElementById("lastUpdated"),
  refreshBtn: document.getElementById("refreshBtn"),
  prevBtn: document.getElementById("prevBtn"),
  nextBtn: document.getElementById("nextBtn"),
  pageInfo: document.getElementById("pageInfo"),
  statHits: document.getElementById("statHits"),
  statShowing: document.getElementById("statShowing"),
  statCity: document.getElementById("statCity"),
  statSchedule: document.getElementById("statSchedule"),
  detailEmpty: document.getElementById("detailEmpty"),
  detailBody: document.getElementById("detailBody"),
  shell: document.querySelector(".shell"),
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function htmlToSafeProse(value) {
  if (!value) return "—";
  const withBreaks = String(value)
    .replace(/<\s*br\s*\/?>/gi, "\n")
    .replace(/<\/\s*p\s*>/gi, "\n\n")
    .replace(/<\/\s*li\s*>/gi, "\n")
    .replace(/<[^>]+>/g, "");
  const decoded = withBreaks
    .replaceAll("&nbsp;", " ")
    .replaceAll("&amp;", "&")
    .replaceAll("&lt;", "<")
    .replaceAll("&gt;", ">")
    .replaceAll("&quot;", '"')
    .replaceAll("&#39;", "'");
  return escapeHtml(decoded).replaceAll("\n", "<br>");
}

function formatNumber(n) {
  return new Intl.NumberFormat("en-GB").format(n ?? 0);
}

function topKey(obj) {
  const entries = Object.entries(obj || {});
  if (!entries.length) return "—";
  return entries[0][0];
}

function buildFacets(jobs) {
  const cities = {};
  const schedules = {};
  jobs.forEach((job) => {
    if (job.city) cities[job.city] = (cities[job.city] || 0) + 1;
    if (job.schedule) schedules[job.schedule] = (schedules[job.schedule] || 0) + 1;
  });
  const sortObj = (obj) =>
    Object.fromEntries(Object.entries(obj).sort((a, b) => b[1] - a[1]).slice(0, 12));
  return {
    categories: jobs.length ? { "Warehouse Operative": jobs.length } : {},
    cities: sortObj(cities),
    schedules: sortObj(schedules),
    businesses: jobs.length ? { "fulfillment-operations": jobs.length } : {},
  };
}

function setLoading(isLoading) {
  state.loading = isLoading;
  els.shell.classList.toggle("loading", isLoading);
  els.refreshBtn.disabled = isLoading;
  els.prevBtn.disabled = isLoading || state.offset <= 0;
  els.nextBtn.disabled = isLoading || state.offset + state.limit >= state.hits;
}

function stampLabel() {
  if (!state.updatedAt) return "Cached feed";
  const date = new Date(state.updatedAt);
  if (Number.isNaN(date.getTime())) return `Updated ${state.updatedAt}`;
  return `Updated ${date.toLocaleString([], { dateStyle: "medium", timeStyle: "short" })}`;
}

function filteredJobs() {
  const city = els.city.value.trim().toLowerCase();
  const schedule = els.schedule.value.toLowerCase();
  return state.allJobs.filter((job) => {
    const hay = `${job.city || ""} ${job.state || ""} ${job.location || ""}`.toLowerCase();
    const cityOk = !city || hay.includes(city);
    const scheduleOk = !schedule || (job.schedule || "").toLowerCase().includes(schedule);
    return cityOk && scheduleOk;
  });
}

function renderFromCache() {
  const filtered = filteredJobs();
  state.hits = filtered.length;
  state.jobs = filtered.slice(state.offset, state.offset + state.limit);
  const facets = buildFacets(state.jobs);

  renderStats({ hits: state.hits, facets });
  renderList();
  renderPager();
  els.lastUpdated.textContent = stampLabel();
  els.statusLine.textContent =
    state.jobs.length > 0
      ? `${formatNumber(state.hits)} Warehouse Operative openings`
      : "No Warehouse Operative openings matched";

  if (state.jobs.length && !state.jobs.some((j) => j.id === state.selectedId)) {
    selectJob(state.jobs[0].id);
  } else if (!state.jobs.length) {
    clearDetail();
  } else {
    selectJob(state.selectedId);
  }
}

async function loadStaticDataset() {
  const res = await fetch(`./jobs.json?t=${Date.now()}`);
  if (!res.ok) throw new Error("jobs.json not found");
  const data = await res.json();
  state.allJobs = data.jobs || [];
  state.updatedAt = data.updated_at || null;
  state.mode = "static";
}

async function loadLiveApi() {
  const params = new URLSearchParams({
    q: "Warehouse Operative",
    country: "GBR",
    sort: "recent",
    offset: "0",
    limit: "100",
  });
  const city = els.city.value.trim();
  const schedule = els.schedule.value;
  if (city) params.set("city", city);
  if (schedule) params.set("schedule", schedule);

  const res = await fetch(`/api/jobs?${params.toString()}`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Request failed");
  state.allJobs = data.jobs || [];
  state.updatedAt = new Date().toISOString();
  state.mode = "live";
}

async function fetchJobs() {
  setLoading(true);
  els.statusLine.textContent =
    state.mode === "live" ? "Scraping Warehouse Operative openings" : "Loading Warehouse Operative openings";

  try {
    try {
      await loadStaticDataset();
    } catch {
      await loadLiveApi();
    }
    renderFromCache();
  } catch (err) {
    els.jobList.innerHTML = `<div class="error-state">${escapeHtml(err.message)}</div>`;
    els.statusLine.textContent = "Load failed";
    els.lastUpdated.textContent = "Error";
    clearDetail();
  } finally {
    setLoading(false);
  }
}

function renderStats(data) {
  els.statHits.textContent = formatNumber(data.hits);
  els.statShowing.textContent = `${state.jobs.length}`;
  els.statCity.textContent = topKey(data.facets?.cities);
  els.statSchedule.textContent = topKey(data.facets?.schedules);
}

function renderList() {
  if (!state.jobs.length) {
    els.jobList.innerHTML = `<div class="empty-state">No Warehouse Operative jobs found right now. Try another city or check back after the next hourly refresh.</div>`;
    return;
  }

  els.jobList.innerHTML = state.jobs
    .map((job, index) => {
      const active = job.id === state.selectedId ? "active" : "";
      return `
        <button class="job-card ${active}" type="button" data-id="${escapeHtml(job.id)}" style="animation-delay:${index * 30}ms" role="listitem">
          <h3>${escapeHtml(job.title)}</h3>
          <div class="job-meta">
            <span>${escapeHtml(job.location || "Location TBD")}</span>
            ${job.pay ? `<span class="tag amber">${escapeHtml(job.pay)}</span>` : ""}
            <span class="tag">${escapeHtml(job.schedule || "schedule TBA")}</span>
          </div>
        </button>
      `;
    })
    .join("");

  els.jobList.querySelectorAll(".job-card").forEach((card) => {
    card.addEventListener("click", () => selectJob(card.dataset.id));
  });
}

function renderPager() {
  const page = Math.floor(state.offset / state.limit) + 1;
  const pages = Math.max(1, Math.ceil(state.hits / state.limit));
  els.pageInfo.textContent = `Page ${page} of ${formatNumber(pages)}`;
  els.prevBtn.disabled = state.loading || state.offset <= 0;
  els.nextBtn.disabled = state.loading || state.offset + state.limit >= state.hits;
}

function clearDetail() {
  state.selectedId = null;
  els.detailEmpty.classList.remove("hidden");
  els.detailBody.classList.add("hidden");
  els.detailBody.innerHTML = "";
}

function selectJob(id) {
  const job = state.jobs.find((j) => j.id === id);
  if (!job) {
    clearDetail();
    return;
  }

  state.selectedId = id;
  els.jobList.querySelectorAll(".job-card").forEach((card) => {
    card.classList.toggle("active", card.dataset.id === id);
  });

  els.detailEmpty.classList.add("hidden");
  els.detailBody.classList.remove("hidden");
  els.detailBody.innerHTML = `
    <div>
      <h2>${escapeHtml(job.title)}</h2>
      <div class="job-meta" style="margin-top:0.55rem">
        <span>${escapeHtml(job.location)}</span>
        <span class="tag">${escapeHtml(job.company)}</span>
        ${job.pay ? `<span class="tag amber">${escapeHtml(job.pay)}</span>` : ""}
        <span class="tag">${escapeHtml(job.schedule || "schedule TBA")}</span>
      </div>
    </div>
    <div class="detail-actions">
      <a class="btn btn-primary" href="${escapeHtml(job.apply_url || job.url)}" target="_blank" rel="noopener noreferrer">Apply on Amazon</a>
      <a class="btn btn-ghost" href="${escapeHtml(job.url)}" target="_blank" rel="noopener noreferrer">Open posting</a>
    </div>
    <section class="detail-section">
      <h3>Summary</h3>
      <div class="prose">${htmlToSafeProse(job.description_short || "No short description provided.")}</div>
    </section>
    <section class="detail-section">
      <h3>Role</h3>
      <div class="prose">${htmlToSafeProse(job.description || "No description scraped.")}</div>
    </section>
    <section class="detail-section">
      <h3>Requirements</h3>
      <div class="prose">${htmlToSafeProse(job.basic_qualifications)}</div>
    </section>
  `;
}

els.form.addEventListener("submit", (event) => {
  event.preventDefault();
  state.offset = 0;
  if (state.allJobs.length) {
    renderFromCache();
  } else {
    fetchJobs();
  }
});

els.refreshBtn.addEventListener("click", () => {
  state.offset = 0;
  fetchJobs();
});

els.prevBtn.addEventListener("click", () => {
  state.offset = Math.max(0, state.offset - state.limit);
  renderFromCache();
});

els.nextBtn.addEventListener("click", () => {
  state.offset += state.limit;
  renderFromCache();
});

fetchJobs();
