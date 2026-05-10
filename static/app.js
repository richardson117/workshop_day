const state = { meta: null, overview: null };
const el = (id) => document.getElementById(id);

async function getJson(url) {
  const response = await fetch(url);
  return response.json();
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return response.json();
}

function score(value, label) {
  const item = document.createElement("article");
  item.className = "score-card";
  item.innerHTML = `<strong>${value}</strong><span>${label}</span>`;
  return item;
}

function fillFilters() {
  const selectedGeo = el("geoSelect").value || "AU";
  el("geoSelect").replaceChildren(
    ...state.meta.geos.map((geo) => {
      const option = document.createElement("option");
      option.value = geo.code;
      option.textContent = `${geo.code}${geo.proxy_ready ? " live-ready" : " replay-ready"}`;
      option.selected = geo.code === selectedGeo;
      return option;
    }),
  );
  const selectedBrand = el("brandSelect").value || "all";
  const brandOptions = [{ name: "all" }, ...state.meta.brands];
  el("brandSelect").replaceChildren(
    ...brandOptions.map((brand) => {
      const option = document.createElement("option");
      option.value = brand.name;
      option.textContent = brand.name === "all" ? "All brands" : brand.name;
      option.selected = brand.name === selectedBrand;
      return option;
    }),
  );
}

function renderPills(target, rows) {
  const nodes = rows.map(([name, count]) => {
    const pill = document.createElement("span");
    pill.className = "pill";
    pill.textContent = `${name}: ${count}`;
    return pill;
  });
  target.replaceChildren(...nodes);
}

function renderNewDiff(diff) {
  const entries = Object.entries(diff || {});
  if (!entries.length) {
    el("newDiff").innerHTML = `<div class="empty">No added or removed games in the New section.</div>`;
    return;
  }
  const nodes = entries.map(([brand, change]) => {
    const item = document.createElement("article");
    item.className = "change-card";
    const added = change.added.map((game) => game.title).slice(0, 5).join(", ") || "none";
    const removed = change.removed.map((game) => game.title).slice(0, 5).join(", ") || "none";
    item.innerHTML = `
      <strong>${brand}</strong>
      <p><b>Added:</b> ${added}</p>
      <p><b>Removed:</b> ${removed}</p>
    `;
    return item;
  });
  el("newDiff").replaceChildren(...nodes);
}

function renderGames(games) {
  el("gameCount").textContent = games.length;
  const rows = games.map((game) => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${game.brand}</td>
      <td>${game.category_label || game.category || game.canonical}</td>
      <td>${game.position}</td>
      <td>${game.title}</td>
      <td>${game.provider || "Unknown"}</td>
    `;
    return row;
  });
  el("gamesTable").replaceChildren(...rows);
}

function currentParams() {
  const params = new URLSearchParams();
  params.set("geo", el("geoSelect").value || "AU");
  params.set("brand", el("brandSelect").value || "all");
  params.set("search", el("searchInput").value || "");
  return params;
}

async function loadOverview() {
  const data = await getJson(`/api/overview?${currentParams().toString()}`);
  state.overview = data;
  if (data.error) {
    el("runProof").textContent = data.error;
    return;
  }
  el("runProof").textContent = `${data.run.geo_code} | ${data.run.run_at} | ${data.proxy.country || "no geo proof"} / ${data.proxy.city || "unknown city"}`;
  el("scoreGrid").replaceChildren(
    score(data.stats.games, "Game placements"),
    score(data.stats.new_section_games, "New section"),
    score(data.stats.brands, "Brands"),
    score(data.stats.providers, "Providers"),
  );
  el("newCount").textContent = `${data.stats.new_section_games} games`;
  renderNewDiff(data.new_section_diff);
  renderPills(el("groupsList"), data.groups);
  renderPills(el("providersList"), data.top_providers);
  renderGames(data.games);
}

async function refreshMeta() {
  state.meta = await getJson("/api/meta");
  fillFilters();
}

async function runScan() {
  el("scanButton").disabled = true;
  el("scanButton").textContent = "Scanning...";
  const result = await postJson("/api/scan", { geo: el("geoSelect").value || "AU" });
  if (result.error) {
    alert(result.error);
  } else {
    alert("Scan started. Refresh in a minute to see the new run.");
  }
  el("scanButton").disabled = false;
  el("scanButton").textContent = "Run live scan";
}

async function saveProxy() {
  const result = await postJson("/api/proxy-env", {
    GEO_PROXY_AU: el("proxyAuInput").value,
    GEO_PROXY_DE: el("proxyDeInput").value,
  });
  const ready = result.ready || {};
  el("proxyStatus").textContent = `Saved. AU: ${ready.GEO_PROXY_AU ? "ready" : "missing"} / DE: ${ready.GEO_PROXY_DE ? "ready" : "missing"}`;
  await refreshMeta();
}

async function boot() {
  await refreshMeta();
  await loadOverview();
  ["geoSelect", "brandSelect"].forEach((id) => el(id).addEventListener("change", loadOverview));
  el("searchInput").addEventListener("input", loadOverview);
  el("scanButton").addEventListener("click", runScan);
  el("saveProxyButton").addEventListener("click", saveProxy);
}

boot();
