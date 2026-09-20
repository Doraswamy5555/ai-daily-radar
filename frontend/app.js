const state = { items: [], stats: null, category: "", search: "", user: null };
const categories = ["models", "tools", "research", "funding", "companies", "other"];
const colors = ["#82a8ff", "#71d2bd", "#e6bd77", "#c79af1", "#f08d9d", "#77869c"];

const feed = document.querySelector("#feed");
const tooltip = document.querySelector("#tooltip");
const chartTargets = ["activity-chart", "category-chart", "source-chart", "relevance-chart"];

function request(path) {
  return fetch(path).then((response) => {
    if (!response.ok) throw new Error("The API request was unsuccessful.");
    return response.json();
  });
}

async function apiRequest(path, method, body) {
  const response = await fetch(path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "We could not complete that request.");
  }
  return response.status === 204 ? null : response.json();
}

async function loadDashboard({ refresh = false } = {}) {
  document.body.classList.add("is-loading");
  renderLoading();
  try {
    const itemPath = state.category ? `/items?category=${encodeURIComponent(state.category)}` : "/items";
    const items = await request(itemPath);
    const stats = refresh || !state.stats ? await request("/stats") : state.stats;
    state.stats = stats;
    state.items = items;
    document.querySelector("#status-text").textContent = "Radar synchronized";
    renderDashboard();
  } catch (_) {
    document.querySelector("#status-text").textContent = "Connection unavailable";
    renderError();
  } finally {
    document.body.classList.remove("is-loading");
  }
}

function renderLoading() {
  feed.replaceChildren(...Array.from({ length: 3 }, () => element("div", "skeleton")));
  chartTargets.forEach((id) => document.querySelector(`#${id}`).replaceChildren(element("div", "chart-empty", "Preparing live analytics…")));
  document.querySelector("#kpi-grid").replaceChildren(...Array.from({ length: 6 }, () => element("div", "kpi-card skeleton")));
}

function renderDashboard() {
  renderKpis();
  renderCharts();
  renderFeed();
}

function renderKpis() {
  const stats = state.stats;
  const cards = [
    ["Total AI Updates", stats.total_items], ["High Relevance", stats.high_relevance_items],
    ["AI Models", stats.category_counts.models], ["AI Tools", stats.category_counts.tools],
    ["Research", stats.category_counts.research], ["Funding", stats.category_counts.funding],
  ];
  const grid = document.querySelector("#kpi-grid");
  grid.replaceChildren(...cards.map(([label, value]) => {
    const card = element("article", "kpi-card");
    card.append(element("span", "kpi-label", label));
    const number = element("strong", "kpi-value", "0");
    card.append(number); animateNumber(number, value);
    return card;
  }));
}

function renderCharts() {
  const daily = Object.entries(state.stats.daily_counts);
  renderLineChart("activity-chart", daily);
  renderDonutChart("category-chart", Object.entries(state.stats.category_counts));
  renderBarChart("source-chart", Object.entries(state.stats.source_counts), "Source");
  renderBarChart("relevance-chart", Object.entries(state.stats.relevance_distribution), "Score");
}

function renderFeed() {
  const query = state.search.trim().toLowerCase();
  const visible = state.items.filter((item) => [item.title, item.summary, item.source, item.category].join(" ").toLowerCase().includes(query));
  document.querySelector("#item-count").textContent = `${visible.length} ${visible.length === 1 ? "update" : "updates"}`;
  if (!state.items.length) return renderEmpty("No AI updates yet", "The collector has not stored any updates yet.");
  if (!visible.length) return renderEmpty("No matching AI updates found", "Try a different search or remove the active filter.");
  feed.replaceChildren(...visible.map(createRadarCard));
}

function createRadarCard(item, index) {
  const card = element("article", "radar-card"); card.style.animationDelay = `${Math.min(index * 35, 180)}ms`;
  const top = element("div", "radar-top"); top.append(element("span", "badge", item.category), scoreElement(item.relevance_score));
  const title = element("h3", "", item.title);
  const meta = element("div", "meta-row", `${item.source} · ${formatDate(item.published_at || item.created_at)}`);
  const summary = element("p", "summary", item.summary || "No feed summary was provided for this update.");
  const why = element("p", "why", "Why it matters: "); why.append(document.createTextNode(item.why_it_matters));
  const footer = element("div", "card-footer"); const link = element("a", "article-link", "Read article →"); link.href = item.url; link.target = "_blank"; link.rel = "noopener noreferrer";
  if (item.id) link.addEventListener("click", () => apiRequest(`/items/${item.id}/view`, "POST").catch(() => {}));
  footer.append(link);
  if (item.id) { const save = element("button", "save-button", "Save item"); save.type = "button"; save.addEventListener("click", async () => { try { await apiRequest(`/items/${item.id}/save`, "POST"); save.textContent = "Saved"; } catch (_) { save.textContent = "Could not save"; } }); footer.append(save); }
  card.append(top, title, meta, summary, why, footer); return card;
}

function scoreElement(score) {
  const wrap = element("div", "score"); wrap.append(element("strong", "", `Relevance ${score}/10`)); const bar = element("span", "score-bar");
  for (let i = 1; i <= 10; i += 1) bar.append(element("i", i <= score ? "on" : "")); wrap.append(bar); return wrap;
}

function renderEmpty(title, detail) {
  const box = element("div", "feed-empty"); box.append(element("div", "", "◌"), element("strong", "", title), element("p", "", detail));
  const retry = element("button", "retry-button", "Refresh radar"); retry.type = "button"; retry.addEventListener("click", () => loadDashboard({ refresh: true })); box.append(retry); feed.replaceChildren(box);
}

function renderError() {
  const panel = element("div", "error-panel"); panel.append(element("strong", "", "Unable to connect to AI Daily Radar API"), element("p", "", "Check that the local API is running, then try again."));
  const retry = element("button", "retry-button", "Retry"); retry.type = "button"; retry.addEventListener("click", () => loadDashboard({ refresh: true })); panel.append(retry); feed.replaceChildren(panel);
  chartTargets.forEach((id) => document.querySelector(`#${id}`).replaceChildren(element("div", "chart-empty", "Analytics will appear when the API is available.")));
}

function renderLineChart(id, pairs) {
  const target = document.querySelector(`#${id}`); if (pairs.length < 2) return emptyChart(target, "More than one day of stored updates is needed for a trend.");
  const { canvas, ctx, width, height } = chartCanvas(target); const padding = 28; const values = pairs.map(([, value]) => value); const max = Math.max(...values, 1); const hits = [];
  ctx.strokeStyle = gridColor(); ctx.lineWidth = 1; for (let i = 0; i < 3; i += 1) { const y = padding + (height - padding * 2) * i / 2; ctx.beginPath(); ctx.moveTo(padding, y); ctx.lineTo(width - padding, y); ctx.stroke(); }
  ctx.strokeStyle = colors[0]; ctx.lineWidth = 2.5; ctx.beginPath(); pairs.forEach(([label, value], i) => { const x = padding + (width - padding * 2) * i / (pairs.length - 1); const y = height - padding - value / max * (height - padding * 2); i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); hits.push({ x, y, label: `${label}: ${value} updates` }); }); ctx.stroke();
  hits.forEach(({ x, y }) => { ctx.fillStyle = colors[0]; ctx.beginPath(); ctx.arc(x, y, 3.5, 0, Math.PI * 2); ctx.fill(); }); bindTooltip(canvas, hits);
}

function renderDonutChart(id, pairs) {
  const target = document.querySelector(`#${id}`); const nonzero = pairs.filter(([, value]) => value > 0); if (!nonzero.length) return emptyChart(target, "Category distribution will appear after items are stored.");
  const { canvas, ctx, width, height } = chartCanvas(target); const total = nonzero.reduce((sum, [, value]) => sum + value, 0); const centerX = width / 2, centerY = height / 2 - 5, radius = Math.min(width, height) / 2 - 25; let start = -Math.PI / 2; const hits = [];
  nonzero.forEach(([label, value], i) => { const part = value / total * Math.PI * 2; ctx.strokeStyle = colors[categories.indexOf(label)] || colors[i]; ctx.lineWidth = 22; ctx.beginPath(); ctx.arc(centerX, centerY, radius, start, start + part); ctx.stroke(); const angle = start + part / 2; hits.push({ x: centerX + Math.cos(angle) * radius, y: centerY + Math.sin(angle) * radius, label: `${label}: ${value}` }); start += part; });
  ctx.fillStyle = textColor(); ctx.textAlign = "center"; ctx.font = "700 22px system-ui"; ctx.fillText(String(total), centerX, centerY + 3); ctx.fillStyle = mutedColor(); ctx.font = "11px system-ui"; ctx.fillText("updates", centerX, centerY + 19); target.append(legend(nonzero)); bindTooltip(canvas, hits);
}

function renderBarChart(id, pairs, labelName) {
  const target = document.querySelector(`#${id}`); const nonzero = pairs.filter(([, value]) => value > 0); if (!nonzero.length) return emptyChart(target, `${labelName} distribution will appear after items are stored.`);
  const { canvas, ctx, width, height } = chartCanvas(target); const padding = 27, max = Math.max(...nonzero.map(([, value]) => value)); const gap = 10, barWidth = Math.max(12, (width - padding * 2 - gap * (nonzero.length - 1)) / nonzero.length); const hits = [];
  ctx.strokeStyle = gridColor(); ctx.beginPath(); ctx.moveTo(padding, height - padding); ctx.lineTo(width - padding, height - padding); ctx.stroke(); nonzero.forEach(([name, value], i) => { const x = padding + i * (barWidth + gap), barHeight = value / max * (height - padding * 2); const y = height - padding - barHeight; ctx.fillStyle = colors[i % colors.length]; ctx.fillRect(x, y, barWidth, barHeight); ctx.fillStyle = mutedColor(); ctx.textAlign = "center"; ctx.font = "10px system-ui"; ctx.fillText(name.length > 10 ? `${name.slice(0, 9)}…` : name, x + barWidth / 2, height - 10); hits.push({ x: x + barWidth / 2, y: y + 8, label: `${name}: ${value}` }); }); bindTooltip(canvas, hits);
}

function chartCanvas(target) { target.replaceChildren(); const canvas = document.createElement("canvas"); target.append(canvas); const rect = target.getBoundingClientRect(), ratio = window.devicePixelRatio || 1; canvas.width = rect.width * ratio; canvas.height = rect.height * ratio; const ctx = canvas.getContext("2d"); ctx.scale(ratio, ratio); return { canvas, ctx, width: rect.width, height: rect.height }; }
function emptyChart(target, message) { target.replaceChildren(element("div", "chart-empty", message)); }
function legend(items) { const row = element("div", "legend"); items.forEach(([name, value]) => { const item = element("span"); const dot = element("i"); dot.style.background = colors[categories.indexOf(name)] || colors[0]; item.append(dot, document.createTextNode(`${name}: ${value}`)); row.append(item); }); return row; }
function bindTooltip(canvas, hits) { canvas.addEventListener("mousemove", (event) => { const rect = canvas.getBoundingClientRect(), x = event.clientX - rect.left, y = event.clientY - rect.top; const hit = hits.reduce((best, point) => !best || Math.hypot(point.x - x, point.y - y) < Math.hypot(best.x - x, best.y - y) ? point : best, null); if (!hit || Math.hypot(hit.x - x, hit.y - y) > 42) return hideTooltip(); tooltip.textContent = hit.label; tooltip.style.left = `${event.clientX + 12}px`; tooltip.style.top = `${event.clientY + 12}px`; tooltip.hidden = false; }); canvas.addEventListener("mouseleave", hideTooltip); }
function hideTooltip() { tooltip.hidden = true; }
function animateNumber(node, end) { const start = performance.now(), duration = 520; const frame = (now) => { node.textContent = Math.round(end * Math.min((now - start) / duration, 1)).toLocaleString(); if (now - start < duration) requestAnimationFrame(frame); }; requestAnimationFrame(frame); }
function element(tag, className = "", text = "") { const node = document.createElement(tag); node.className = className; if (text) node.textContent = text; return node; }
function formatDate(value) { const date = new Date(value); return Number.isNaN(date) ? value || "Date unavailable" : new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" }).format(date); }
function gridColor() { return getComputedStyle(document.body).getPropertyValue("--line"); } function mutedColor() { return getComputedStyle(document.body).getPropertyValue("--muted"); } function textColor() { return getComputedStyle(document.body).getPropertyValue("--text"); }

document.querySelectorAll(".filter").forEach((button) => button.addEventListener("click", () => { state.category = button.dataset.category; document.querySelectorAll(".filter").forEach((item) => item.classList.toggle("active", item === button)); loadDashboard(); }));
document.querySelector("#search-input").addEventListener("input", (event) => { state.search = event.target.value; document.querySelector("#clear-search").hidden = !state.search; renderFeed(); });
document.querySelector("#clear-search").addEventListener("click", () => { const input = document.querySelector("#search-input"); input.value = ""; state.search = ""; input.focus(); document.querySelector("#clear-search").hidden = true; renderFeed(); });
document.querySelector("#refresh-button").addEventListener("click", () => loadDashboard({ refresh: true }));
document.querySelector("#theme-toggle").addEventListener("click", () => { document.body.classList.toggle("light"); localStorage.setItem("radar-theme", document.body.classList.contains("light") ? "light" : "dark"); document.querySelector("#theme-toggle").setAttribute("aria-label", document.body.classList.contains("light") ? "Switch to dark theme" : "Switch to light theme"); if (state.stats) renderCharts(); });
if (localStorage.getItem("radar-theme") === "light") document.body.classList.add("light");

function showAuthenticated(user) {
  state.user = user;
  document.querySelector("#auth-gate").hidden = true;
  document.querySelector("#app-header").hidden = false;
  document.querySelector("#dashboard-content").hidden = false;
  document.querySelector("#user-menu").hidden = false;
  document.querySelector("#user-name").textContent = user.name;
  document.querySelector("#menu-user-name").textContent = user.name;
  document.querySelector("#menu-user-email").textContent = user.email;
  document.querySelector("#user-initial").textContent = user.name.charAt(0).toUpperCase();
  document.querySelector("#overview-title").innerHTML = `Welcome back, <em>${escapeHtml(user.name)}.</em>`;
  loadDashboard({ refresh: true });
}

function showAuth() {
  state.user = null; state.items = []; state.stats = null;
  document.querySelector("#auth-gate").hidden = false;
  document.querySelector("#app-header").hidden = true;
  document.querySelector("#dashboard-content").hidden = true;
  document.querySelector("#user-panel").hidden = true;
}

function escapeHtml(value) { const div = document.createElement("div"); div.textContent = value; return div.innerHTML; }

async function bootstrap() {
  try { showAuthenticated(await request("/auth/me")); } catch (_) { showAuth(); }
}

document.querySelectorAll(".auth-tab").forEach((button) => button.addEventListener("click", () => {
  document.querySelectorAll(".auth-tab").forEach((tab) => tab.classList.toggle("active", tab === button));
  document.querySelector("#signin-form").hidden = button.dataset.authView !== "signin";
  document.querySelector("#signup-form").hidden = button.dataset.authView !== "signup";
  document.querySelector("#auth-message").textContent = "";
}));

document.querySelector("#signin-form").addEventListener("submit", async (event) => {
  event.preventDefault(); const form = new FormData(event.currentTarget); const message = document.querySelector("#auth-message");
  try { showAuthenticated(await apiRequest("/auth/login", "POST", { email: form.get("email"), password: form.get("password") })); } catch (error) { message.textContent = error.message; }
});

document.querySelector("#signup-form").addEventListener("submit", async (event) => {
  event.preventDefault(); const form = new FormData(event.currentTarget); const message = document.querySelector("#auth-message");
  const account = { name: form.get("name"), email: form.get("email"), password: form.get("password") };
  try { await apiRequest("/auth/register", "POST", account); showAuthenticated(await apiRequest("/auth/login", "POST", { email: account.email, password: account.password })); } catch (error) { message.textContent = error.message; }
});

async function openUserPanel(kind) {
  const panel = document.querySelector("#user-panel"), content = document.querySelector("#user-panel-content"); panel.hidden = false; content.replaceChildren(element("p", "", "Loading…"));
  if (kind === "preferences") {
    const preferences = await request("/preferences"); const form = document.createElement("form"); form.append(element("h2", "", "Preferences"));
    categories.forEach((category) => { const label = element("label"); const input = document.createElement("input"); input.type = "checkbox"; input.value = category; input.checked = preferences.categories.includes(category); label.append(input, document.createTextNode(category)); form.append(label); });
    const save = element("button", "primary-button", "Save preferences"); save.type = "submit"; form.append(save); form.addEventListener("submit", async (event) => { event.preventDefault(); const selected = [...form.querySelectorAll("input:checked")].map((input) => input.value); await apiRequest("/preferences", "PUT", { categories: selected }); save.textContent = "Preferences saved"; }); content.replaceChildren(form); return;
  }
  const items = await request(kind === "saved" ? "/saved-items" : "/history"); content.append(element("h2", "", kind === "saved" ? "Saved items" : "View history"));
  if (!items.length) content.append(element("p", "", "No items yet."));
  items.forEach((item) => { const entry = element("div", "panel-item"); entry.append(element("strong", "", item.title), element("small", "", item.source)); content.append(entry); });
}

document.querySelectorAll("[data-user-panel]").forEach((button) => button.addEventListener("click", () => openUserPanel(button.dataset.userPanel).catch(() => {})));
document.querySelector("#close-user-panel").addEventListener("click", () => { document.querySelector("#user-panel").hidden = true; });
document.querySelector("#logout-button").addEventListener("click", async () => { await apiRequest("/auth/logout", "POST"); showAuth(); });
bootstrap();
