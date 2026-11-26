// The Almanac: what every number means and exactly where it comes from.
import { resolveTables } from "../terrain.js";
import { esc } from "../format.js";
import { parseHex, luminance } from "../color.js";
import { icon, glyph } from "./icon.js";

const COVER_ICON = { forest_deciduous: "l-forest", forest_evergreen: "l-forest", forest_mixed: "l-forest", cropland: "l-farmland", pasture: "l-farmland", urban: "l-developed" };
// Glyph colour that reads on a resource medallion (dark on light faces such as nuclear yellow or silver).
const inkOn = (hex) => {
  try { return /^#[0-9a-f]{6}$/i.test(hex || "") && luminance(parseHex(hex)) > 0.4 ? "#1c1710" : "#f8f0d8"; } catch { return "#f8f0d8"; }
};
const CATEGORY = { energy: "Energy", mineral: "Minerals", agri: "Agriculture" };

export function initPedia(data) {
  const modal = document.getElementById("pedia");
  const card = modal.querySelector(".modal-card");
  const nav = document.getElementById("pedia-nav");
  const body = document.getElementById("pedia-body");
  const srcName = (id) => data.sources?.find((s) => s.id === id)?.title || id || "";
  let restoreFocus = null;

  const h2 = (ic, fb, text) => `<h2>${icon(ic, fb, { size: 24 })}<span>${esc(text)}</span></h2>`;

  const pages = {
    "About this map": () => `
      ${h2("pedia", "📖", "About this map")}
      <p>This is real <b>Thailand (ประเทศไทย)</b>, drawn like a 4X strategy game. Nothing is invented: every tile, province,
      city and number comes from official Thai and global public datasets, listed under <i>Sources</i>.</p>
      <h4>How it's built</h4>
      <p>All 77 provinces of Thailand are projected (Albers equal-area conic centred on 101°E, 13°N) and cut into
      ${data.world.grid.cols}×${data.world.grid.rows} hexes, each ${data.world.grid.radius * 2} km corner to corner
      (~166 km² per hex). Each hex belongs to the province (จังหวัด) and district (อำเภอ / เขต) under its centre.
      Elevation comes from NOAA ETOPO1 and satellite land cover from ESA WorldCover 10m (2021).</p>
      <p><b>Cities</b> represent Thailand's 77 provincial hubs (with <b>★ Bangkok</b> as national capital), populated with
      official NESDC 2024p Gross Provincial Product (19 sectors), DOPA civil registration (2020–2025), and NSO Socio-Economic
      and Labor Force Surveys.</p>
      <h4>Controls</h4>
      <p>Drag or arrow keys / WASD to pan · scroll, +/– or double-click to zoom · click a city or province to open it ·
      / or ⌘K to search (English or ไทย) · L to cycle lenses · R to show or hide resources · ? for shortcuts · Esc to close.</p>
      <p class="muted">Built on the MIT-licensed <i>usaciv</i> visualization engine by Andrej Karpathy.</p>`,
    Yields: () => `
      ${h2("y-production", "⚙️", "Yields")}
      <p>Civilization's yields mapped directly onto Thailand's official NESDC 2024p Gross Provincial Product (GPP) in Thai Baht (฿).
      <b>Gold is total GPP</b>; Food, Production, Science and Culture represent real economic value added in their respective sectors.</p>
      <table>${data.nation.yields.map((y) => `<tr><td class="ic" style="color:${esc(y.color)}">${glyph(y, 26)}</td><td><b style="color:${esc(y.color)}">${esc(y.label)}${y.key === "gold" ? " (GPP)" : ""}</b><br>${esc(y.description)}</td></tr>`).join("")}</table>
      <h4>Living &amp; Economy</h4>
      <p>Unemployment comes from the NSO Labor Force Survey. Household income, monthly spending, household debt and
      spending-to-income ratios come from the NSO Socio-Economic Survey (SES).</p>`,
    Provinces: () => `
      ${h2("terrain", "🗺️", "Provinces (จังหวัด)")}
      <p>Click any land hex without a city banner to open its province. All <b>77 provinces</b> (76 changwat + Bangkok Metropolis)
      and <b>928 districts (amphoe &amp; Bangkok khet)</b> are mapped from official geoBoundaries / Royal Thai Survey Department outlines.</p>
      <p><b>Ranks</b> ("#1 of 77") compare all 77 provinces of Thailand (1 = largest).</p>`,
    Terrain: () => {
      const t = data.w?.tables || resolveTables(data.world.tables);
      const hasCover = Array.isArray(data.world.cover);
      const row = (x) => `<tr><td class="nm">${x.color ? `<span class="swatch" style="background:${esc(x.color)}"></span>` : ""}${
        COVER_ICON[x.key] ? icon(COVER_ICON[x.key], "", { size: 15 }) + " " : ""}<b>${esc(x.name)}</b></td><td>${esc(x.rule || "")}</td></tr>`;
      return `
      ${h2("terrain", "🗺️", "Terrain")}
      <p>Each 8 km hex averages ETOPO1 elevation samples inside it (from the shallow Gulf of Thailand and Chao Phraya delta
      to Doi Inthanon at 2,565 m). Shading comes from elevation differences with neighbouring hexes, lit from the north-west.</p>
      <h4>${icon("l-forest", "🌲", { size: 16 })} Satellite land cover (ESA WorldCover 2021)</h4>
      ${hasCover
        ? `<p>The base colour of each hex is its dominant satellite land-cover class (tropical rainforest, monsoon deciduous forest,
           rice &amp; cropland, mangroves/wetland, scrub, grassland or built-up urban). Symbols scale with the real pixel mixture inside each hex.</p>
           <table>${t.cover.filter((x) => x.id > 0).map(row).join("")}</table>`
        : `<p class="muted">No land-cover layer loaded.</p>`}
      <h4>Relief</h4>
      <table>${t.relief.map(row).join("")}</table>
      <h4>${icon("r-hydro", "💧", { size: 16 })} Water</h4>
      <table>${t.water.filter((x) => x.id > 0).map(row).join("")}</table>
      <h4>Beyond the borders</h4>
      <p class="muted">Neighbouring countries (Myanmar, Laos, Cambodia, Malaysia and Vietnam) are drawn under a light fog of war for geographic context.</p>`;
    },
    Lenses: () => `
      ${h2("layers", "▤", "Lenses")}
      <p>Lenses recolour Thailand's 3,200+ hexes by a single real measure (${esc(data.lenses.vintage)}). Land lenses show
      true 8 km hex satellite fractions from ESA WorldCover; demographic, economic and hazard lenses show official provincial
      and district statistics.</p>
      <p>The legend shows the distribution of hexes. Hover or drag across it to highlight only that range on the map.</p>
      ${(data.lenses.groups || [{ id: null, name: "" }]).map((g) => {
        const ls = data.lenses.lenses.filter((l) => !g.id || l.group === g.id);
        if (!ls.length) return "";
        return `${g.name ? `<h3 class="grp">${icon(`g-${g.id}`, "", { size: 16 })} ${esc(g.name)}</h3>` : ""}${ls.map((l) => `
          <div class="lens-entry"><div class="le-ic">${glyph(l, 26)}</div><div>
          <h4>${esc(l.name)}</h4><p>${esc(l.description)}<br>
          <i class="le-ramp" style="background:linear-gradient(90deg, ${(l.ramp || []).map(esc).join(",")})"></i>
          <span class="muted">Scale: ${esc(l.scale)}, ${l.domain[0].toLocaleString()}–${l.domain[1].toLocaleString()} ${esc(l.unit)}${
            l.higher_is === "good" ? " · higher is better" : l.higher_is === "bad" ? " · higher is worse" : ""}${l.source ? " · " + esc(srcName(l.source)) : ""}</span></p></div></div>`).join("")}`;
      }).join("")}`,
    Resources: () => {
      const r = data.resources;
      if (!r?.types?.length) return `${h2("resources", "⛏️", "Resources")}<p class="muted">No resources layer.</p>`;
      const count = new Map();
      for (const it of r.items || []) count.set(it.type, (count.get(it.type) || 0) + 1);
      const cats = [...new Set(r.types.map((t) => t.category || "other"))];
      return `
      ${h2("resources", "⛏️", "Resources")}
      <p>Resources mark Thailand's major power plants (natural gas stations, Mae Moh &amp; industrial coal plants, EGAT hydroelectric
      dams, solar farms, Khorat Plateau wind farms and biomass facilities) from the WRI Global Power Plant Database. Press <b>R</b> to toggle.</p>
      ${cats.map((c) => `<h4>${esc(CATEGORY[c] || c)}</h4><table class="res-table">
        <tr><th></th><th>Type</th><th>What counts</th><th>Sites</th></tr>
        ${r.types.filter((t) => (t.category || "other") === c).map((t) => `<tr>
          <td class="ic"><span class="res-ic" style="background:${esc(t.color || "#24384f")};color:${inkOn(t.color)}">${glyph(t, 20)}</span></td>
          <td class="nm"><b>${esc(t.name)}</b>${t.unit ? `<br><span class="muted">value in ${esc(t.unit)}</span>` : ""}</td>
          <td>${esc(t.description || "")}<br><span class="muted">Source: ${esc(srcName(t.source))}</span></td>
          <td class="num">${count.get(t.id) || 0}</td></tr>`).join("")}</table>`).join("")}`;
    },
    Sources: () => `
      ${h2("pedia", "📖", "Sources")}
      ${data.sources.map((s) => `
        <h4>${esc(s.title)}</h4>
        <p>${esc(s.description)}<br>
        <span class="muted">${esc(s.publisher)} · ${esc(s.license)}${s.vintage ? " · " + esc(s.vintage) : ""} ·
        <a href="${esc(s.homepage)}" target="_blank" rel="noopener">homepage</a></span></p>
        <table>${(s.files || []).map((f) => `<tr><td><code>${esc(f.url)}</code></td><td class="muted" style="white-space:nowrap">${esc((f.retrieved || "").slice(0, 10))}<br>${((f.bytes || 0) / 1e6).toFixed(1)} MB</td></tr>`).join("")}</table>`).join("")}`,
  };

  const show = (name) => {
    if (!pages[name]) name = "About this map";
    body.innerHTML = pages[name]();
    body.scrollTop = 0;
    nav.querySelectorAll("button").forEach((b) => {
      const on = b.dataset.page === name;
      b.classList.toggle("active", on);
      b.setAttribute("aria-current", on ? "page" : "false");
    });
  };
  nav.innerHTML = `<div class="hd">Almanac</div>` + Object.keys(pages).map((p) => `<button data-page="${esc(p)}">${esc(p)}</button>`).join("");
  nav.onclick = (e) => {
    const b = e.target.closest("button[data-page]");
    if (b) show(b.dataset.page);
  };
  const close = () => {
    if (modal.hidden) return;
    modal.hidden = true;
    if (restoreFocus && document.contains(restoreFocus)) restoreFocus.focus();
    restoreFocus = null;
  };
  modal.onclick = (e) => {
    if (e.target === modal || e.target.closest("[data-close]")) close();
  };
  // Keep Tab inside the dialog.
  modal.addEventListener("keydown", (e) => {
    if (e.key !== "Tab") return;
    const f = [...card.querySelectorAll("button, a[href], [tabindex]:not([tabindex='-1'])")].filter((x) => x.offsetParent);
    if (!f.length) return;
    const first = f[0], last = f[f.length - 1];
    if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
    else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
  });

  return {
    open(page = "About this map") {
      if (modal.hidden) restoreFocus = document.activeElement;
      show(page);
      modal.hidden = false;
      (nav.querySelector("button.active") || card.querySelector("[data-close]"))?.focus();
    },
    close,
    get isOpen() {
      return !modal.hidden;
    },
  };
}
