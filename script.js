const listingGrid = document.getElementById("listingGrid");
const filterGroup = document.getElementById("filterGroup");
const dynamicFilters = document.getElementById("dynamicFilters");
const listingHeading = document.getElementById("listingHeading");
const resourceList = document.getElementById("resourceList");
const pagination = document.getElementById("pagination");

const statsTotal = document.getElementById("statsTotal");
const statsSources = document.getElementById("statsSources");
const statsUpdated = document.getElementById("statsUpdated");

const featuredTitle = document.getElementById("featuredTitle");
const featuredDescription = document.getElementById("featuredDescription");
const featuredPills = document.getElementById("featuredPills");
const featuredLink = document.getElementById("featuredLink");

const dataBundle = window.__JOB_DATA__ || {
  generatedAt: null,
  totalJobs: 0,
  sourceCounts: [],
  featuredJob: null,
  resourceJobs: [],
  jobs: []
};

const PAGE_SIZE = 12;
let currentFilter = "all";
let currentPage = 1;

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;"
  }[char]));
}

function formatDateLabel(dateString) {
  if (!dateString) {
    return "No refresh yet";
  }

  const date = new Date(dateString.replace(" ", "T"));

  if (Number.isNaN(date.getTime())) {
    return dateString;
  }

  return date.toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric"
  });
}

function renderStats() {
  statsTotal.textContent = dataBundle.totalJobs;
  statsSources.textContent = `${dataBundle.sourceCounts.length} sources`;
  statsUpdated.textContent = formatDateLabel(dataBundle.generatedAt);
}

function renderSourceFilters() {
  const sources = dataBundle.sourceCounts
    .map((item) => item.source)
    .filter(Boolean)
    .sort((left, right) => left.localeCompare(right));

  dynamicFilters.innerHTML = sources.map((source) => `
    <button class="filter-chip" data-filter="${escapeHtml(source.toLowerCase())}">
      ${escapeHtml(source)}
    </button>
  `).join("");
}

function renderFeatured() {
  const job = dataBundle.featuredJob;

  if (!job) {
    return;
  }

  featuredTitle.textContent = job.title;
  featuredDescription.textContent = job.description;
  featuredPills.innerHTML = [
    `<span class="pill">${escapeHtml(job.source)}</span>`,
    `<span class="pill">${escapeHtml(job.type)}</span>`,
    `<span class="pill">${job.pdf ? "PDF Available" : "Official Link"}</span>`
  ].join("");
  featuredLink.href = job.link;
  featuredLink.target = "_blank";
  featuredLink.rel = "noreferrer";
  featuredLink.textContent = job.pdf ? "Open PDF Notice" : "Open Official Update";
}

function renderResources() {
  const pdfJobs = dataBundle.resourceJobs;

  if (!pdfJobs.length) {
    resourceList.innerHTML = `
      <li>
        <div>
          <strong>No PDF notices found</strong>
          <span>Run the scraper again after new notices are published.</span>
        </div>
        <a href="#notifications">Open alerts</a>
      </li>
    `;
    return;
  }

  resourceList.innerHTML = pdfJobs.map((job) => `
    <li>
      <div>
        <strong>${escapeHtml(job.title)}</strong>
        <span>${escapeHtml(job.source)} PDF notice</span>
      </div>
      <a href="${escapeHtml(job.link)}" target="_blank" rel="noreferrer">Download PDF</a>
    </li>
  `).join("");
}

function getFilteredJobs(filter) {
  if (filter === "all") {
    return dataBundle.jobs;
  }

  if (filter === "pdf") {
    return dataBundle.jobs.filter((job) => job.pdf);
  }

  return dataBundle.jobs.filter((job) => job.tag === filter);
}

function renderPagination(totalItems) {
  const totalPages = Math.max(1, Math.ceil(totalItems / PAGE_SIZE));

  if (totalItems <= PAGE_SIZE) {
    pagination.innerHTML = "";
    return;
  }

  const pageButtons = Array.from({ length: totalPages }, (_, index) => {
    const page = index + 1;

    return `
      <button
        class="pagination-button ${page === currentPage ? "is-active" : ""}"
        data-page="${page}"
        type="button"
      >
        ${page}
      </button>
    `;
  }).join("");

  pagination.innerHTML = `
    <button
      class="pagination-button pagination-nav"
      data-page="${Math.max(1, currentPage - 1)}"
      type="button"
      ${currentPage === 1 ? "disabled" : ""}
    >
      Previous
    </button>
    <div class="pagination-pages">${pageButtons}</div>
    <button
      class="pagination-button pagination-nav"
      data-page="${Math.min(totalPages, currentPage + 1)}"
      type="button"
      ${currentPage === totalPages ? "disabled" : ""}
    >
      Next
    </button>
  `;
}

function renderListings(filter = currentFilter, page = currentPage) {
  const filtered = getFilteredJobs(filter);
  const filterLabel = filter === "all" ? "All Live Alerts" : filter.toUpperCase();
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));

  currentFilter = filter;
  currentPage = Math.min(page, totalPages);

  const start = (currentPage - 1) * PAGE_SIZE;
  const paginated = filtered.slice(start, start + PAGE_SIZE);

  listingHeading.textContent = `${filterLabel} (${filtered.length})`;

  if (!filtered.length) {
    listingGrid.innerHTML = `
      <article class="listing-card listing-card-empty">
        <h3>No alerts found for this filter</h3>
        <p>Try another source filter or refresh the scraper export.</p>
      </article>
    `;
    pagination.innerHTML = "";
    return;
  }

  listingGrid.innerHTML = paginated.map((item, index) => `
    <article class="listing-card" style="animation-delay: ${index * 50}ms">
      <div class="listing-meta">
        <span class="meta-tag">${escapeHtml(item.type)}</span>
        <span class="meta-tag">${escapeHtml(item.scope)}</span>
        ${item.pdf ? '<span class="meta-tag">PDF</span>' : ""}
      </div>
      <h3>${escapeHtml(item.title)}</h3>
      <p>${escapeHtml(item.description)}</p>
      <strong>${escapeHtml(item.publishedLabel)}</strong>
      <div class="listing-actions">
        <a class="action-primary" href="${escapeHtml(item.link)}" target="_blank" rel="noreferrer">Open Source</a>
        <a class="action-secondary" href="${escapeHtml(item.link)}" target="_blank" rel="noreferrer">${item.pdf ? "View PDF" : "Visit Notice"}</a>
      </div>
    </article>
  `).join("");

  renderPagination(filtered.length);
}

filterGroup.addEventListener("click", (event) => {
  const button = event.target.closest(".filter-chip");

  if (!button) {
    return;
  }

  document.querySelectorAll(".filter-chip").forEach((chip) => {
    chip.classList.remove("is-active");
  });

  button.classList.add("is-active");
  renderListings(button.dataset.filter, 1);
});

pagination.addEventListener("click", (event) => {
  const button = event.target.closest(".pagination-button");

  if (!button || button.disabled) {
    return;
  }

  renderListings(currentFilter, Number(button.dataset.page));
});

renderStats();
renderSourceFilters();
renderFeatured();
renderResources();
renderListings();

// Update the stats with current date
document.getElementById("statsUpdated").innerText =
  "Updated on " + new Date().toLocaleDateString();

window.addEventListener("load", () => {
  if (window.adsbygoogle) {
    window.adsbygoogle.push({});
  }
});
