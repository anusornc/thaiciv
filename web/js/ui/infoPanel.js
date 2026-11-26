// Shared building blocks for the city and state panels (both render into #city-panel).
import { compact, dollars, esc, int, money, pct, yieldValue } from "../format.js";
import { icon, glyph } from "./icon.js";
import { t, yieldLabel, yieldDesc, industryName } from "../i18n.js";

// Industry → a "district" glyph: SVG icons i-<key> from icons.js; these emoji are only the fallback.
export const DISTRICT_ICON = {
  agriculture: "🌾", mining: "⛏️", construction: "🏗️", manufacturing: "🏭", trade: "🛍️", wholesale: "📦", retail: "🛍️",
  transportation: "🚢", utilities: "⚡", water_waste: "💧", information: "📡", finance: "🏦", real_estate: "🏘️", professional: "🔬",
  management: "🏢", admin: "🗂️", education: "🎓", health: "🏥", arts: "🎭", accommodation: "🍽️", other: "🔧",
  public_admin: "🏛️",
};

const panelEl = () => document.getElementById("city-panel");

// Yield tiles; `ranks` (optional) adds "#3 of 49" under each.
export function yieldGrid(nation, yields, ranks = null, rankOf = 0) {
  return nation.yields
    .map((y) => {
      const v = yields?.[y.key];
      const r = ranks?.[y.key];
      const label = yieldLabel(y.key, y.key === "gold" ? "GPP" : y.label);
      const desc = yieldDesc(y.key, y.description || "");
      return `<div class="yield-tile" title="${esc(label)}: ${esc(desc)}">
        <div class="ico" style="color:${esc(y.color)}">${glyph(y, 20)}</div>
        <div class="val" style="color:${esc(y.color)}">${yieldValue(y, v)}</div>
        <div class="lbl">${esc(label)}</div>
        ${r ? `<div class="rank" title="${t(`Rank among Thailand's ${rankOf} provinces (1 = largest)`, `อันดับจาก ${rankOf} จังหวัดของไทย (1 = สูงสุด)`)}">#${r} ${t(`of ${rankOf}`, `/ ${rankOf}`)}</div>` : ""}</div>`;
    })
    .join("");
}

// One "value ▲ TH value" row. higherIsGood: true / false / null (neutral).
export function statRow(ic, fallback, label, v, nv, fmt, higherIsGood) {
  let cmp = "";
  if (v != null && nv != null && nv !== 0) {
    const ratio = v / nv;
    const cls = Math.abs(ratio - 1) < 0.03 || higherIsGood == null ? "" : (higherIsGood ? ratio >= 1 : ratio <= 1) ? "good" : "bad";
    const arrow = Math.abs(ratio - 1) < 0.03 ? "≈" : ratio > 1 ? "▲" : "▼";
    cmp = `<span class="cmp ${cls}">${arrow} ${t("TH", "ไทย")} ${fmt(nv)}</span>`;
  }
  return `<div class="stat-row"><span class="sl">${icon(ic, fallback, { size: 14 })}${esc(label)}</span><span><b>${fmt(v)}</b>${cmp}</span></div>`;
}

export function amenities(o, n) {
  return `
    ${statRow("unemployment", "😐", t("Unemployment", "อัตราการว่างงาน"), o.unemployment, n.unemployment, (x) => pct(x), false)}
    ${statRow("l-income", "💵", t("Annual household income", "รายได้ครัวเรือนต่อปี"), o.median_income, n.median_income, dollars, true)}
    ${statRow("l-home", "🏠", t("Avg. household debt", "หนี้สินเฉลี่ยต่อครัวเรือน"), o.home_value, n.home_value, dollars, false)}
    ${statRow("l-homeownership", "🔑", t("Monthly household spending", "รายจ่ายครัวเรือนต่อเดือน"), o.median_rent, n.median_rent, dollars, null)}
    ${statRow(null, "⚖️", t("Spending ÷ income", "สัดส่วนรายจ่ายต่อรายได้"), o.rent_burden, n.rent_burden, (x) => pct(x), false)}`;
}

// Sector output with location quotients vs. Thailand ("specialisation"). limit = max rows (0 = all).
export function industries(o, nation, limit = 0) {
  const n = nation.nation;
  const total = Object.values(o.jobs || {}).reduce((a, b) => a + (b > 0 ? b : 0), 0) || 1;
  const nTotal = Object.values(n.jobs || {}).reduce((a, b) => a + (b > 0 ? b : 0), 0) || 1;
  let rows = Object.entries(o.jobs || {})
    .filter(([, v]) => v > 0)
    .sort((a, b) => b[1] - a[1]);
  if (limit) rows = rows.slice(0, limit);
  if (!rows.length) return `<p class="muted">${t("No sector data.", "ไม่มีข้อมูลรายสาขา")}</p>`;
  const maxShare = rows[0][1] / total;
  return rows
    .map(([k, v]) => {
      const share = v / total;
      const nShare = (n.jobs?.[k] || 0) / nTotal;
      const lq = nShare > 0 ? share / nShare : 1;
      const tip = t(`Share of GPP is ${lq.toFixed(1)}× Thailand's national share`, `สัดส่วน GPP สูงเป็น ${lq.toFixed(1)} เท่าของค่าเฉลี่ยประเทศ`);
      const badge = lq >= 1.3 ? `<span class="lq hi" title="${tip}">×${lq.toFixed(1)}</span>`
        : lq <= 0.6 ? `<span class="lq lo" title="${tip}">×${lq.toFixed(1)}</span>` : "";
      const icKey = k === "trade" ? "i-retail" : k === "water_waste" ? "i-utilities" : `i-${k}`;
      return `<div class="ind"><span aria-hidden="true">${icon(icKey, DISTRICT_ICON[k] || "•")}</span>
        <span>${esc(industryName(k, nation.industries?.[k] || k))}${badge}</span><span class="n">฿${compact(v * 1e6)} · ${pct(share, 0)}</span>
        <div class="bar"><i style="width:${(share / maxShare) * 100}%;background:${lq >= 1.3 ? "#9fd76a" : "#c9a45c"}"></i></div></div>`;
    })
    .join("");
}

export const gdpRow = (o) =>
  o.gdp != null
    ? `<div class="stat-row"><span class="sl">${icon("y-gold", "💰", { size: 14 })}GPP${o.gdp_year ? ` (${o.gdp_year})` : ""}</span><span><b>${money(o.gdp)}</b>${
        o.population ? `<span class="cmp">${money(o.gdp / o.population)} ${t("per person", "/ คน")}</span>` : ""}</span></div>`
    : "";

export function growthSpan(o, n = null) {
  if (!Number.isFinite(o?.growth)) return "";
  const yrs = Array.isArray(o.growth_years) && o.growth_years.length === 2 ? o.growth_years : null;
  const p = (g) => `${g >= 0 ? "+" : "−"}${Math.abs(g * 100).toFixed(1)}%`;
  const period = yrs ? `${yrs[0]}–${yrs[1]}` : t("the last few years", "ช่วงไม่กี่ปีที่ผ่านมา");
  const th = Number.isFinite(n?.growth) ? ` (${t("Thailand", "ไทย")} ${p(n.growth)})` : "";
  const tip = t(`Registered population change ${period}, DOPA Civil Registration: ${p(o.growth)}${th}`, `การเปลี่ยนแปลงประชากรทะเบียนราษฎร ${period}: ${p(o.growth)}${th}`);
  const cls = o.growth >= 0 ? "good" : "bad";
  return ` · <span class="growth ${cls}" title="${esc(tip)}">${o.growth >= 0 ? "▲" : "▼"} ${Math.abs(o.growth * 100).toFixed(1)}%${
    yrs ? ` <span class="since">${t(`since ${yrs[0]}`, `ตั้งแต่ ${yrs[0]}`)}</span>` : ""}</span>`;
}

export const popLine = (o, extra = "") =>
  `<div class="cp-pop">${icon("pop", "👥", { size: 16 })} <b>${int(o.population)}</b> ${t("people", "คน")} · ${int(o.employed)} ${t("employed", "มีงานทำ")}${extra}</div>`;

/**
 * Fill and show the panel.
 * spec: {kind: "city"|"state", stripe, title, sub, headExtra, sections: [{title, html}], foot, onClose, onPedia, wire(panel)}
 */
export function showPanel(spec) {
  const panel = panelEl();
  panel.dataset.kind = spec.kind;
  const kindLbl = spec.kind === "state" ? t("Province", "จังหวัด") : t("City", "เมืองหลัก");
  panel.setAttribute("aria-label", `${kindLbl}: ${spec.title}`);
  panel.innerHTML = `
    <div class="sheet-grip" aria-hidden="true"></div>
    <div class="cp-head">
      <div class="stripe" style="background:${spec.stripe}"></div>
      <button class="icon-btn cp-close" aria-label="${t("Close panel (Esc)", "ปิดหน้าต่าง (Esc)")}" title="${t("Close (Esc)", "ปิด (Esc)")}">${icon("close", "✕", { size: 13 })}</button>
      <div class="cp-kind">${esc(kindLbl)}</div>
      <h2 class="cp-name">${spec.titleHtml ?? esc(spec.title)}</h2>
      ${spec.sub ? `<div class="cp-full">${spec.sub}</div>` : ""}
      ${spec.headExtra || ""}
    </div>
    ${spec.sections.filter(Boolean).map((s) => `<section class="cp-section"><h3>${s.title}</h3>${s.html}</section>`).join("")}
    <div class="cp-foot">${spec.foot || ""} <a href="#" data-pedia>${t("Almanac ›", "สารานุกรม ›")}</a></div>`;
  panel.hidden = false;
  panel.scrollTop = 0;
  panel.classList.remove("dragging-sheet");
  panel.style.transform = "";
  document.body.classList.add("panel-open");
  panel.querySelector(".cp-close").onclick = spec.onClose;
  panel.querySelector("[data-pedia]").onclick = (e) => {
    e.preventDefault();
    spec.onPedia?.();
  };
  spec.wire?.(panel);
}

export function hidePanel() {
  const panel = panelEl();
  panel.hidden = true;
  panel.innerHTML = "";
  delete panel.dataset.kind;
  document.body.classList.remove("panel-open");
}

// Bottom-sheet swipe-down to close (mobile). Installed once.
export function installSheetSwipe(onClose) {
  const panel = panelEl();
  let start = null;
  panel.addEventListener("pointerdown", (e) => {
    if (e.pointerType === "mouse" || !matchMedia("(max-width: 700px)").matches) return;
    // Only from the grip/head, or anywhere while the sheet is scrolled to the top.
    const fromHead = e.target.closest(".sheet-grip, .cp-head");
    if (!fromHead && panel.scrollTop > 0) return;
    if (e.target.closest("button, a, input")) return;
    start = { y: e.clientY, id: e.pointerId, dy: 0, head: !!fromHead };
  });
  panel.addEventListener("pointermove", (e) => {
    if (!start || e.pointerId !== start.id) return;
    start.dy = Math.max(0, e.clientY - start.y);
    if (start.dy > 6 && (start.head || panel.scrollTop <= 0)) {
      panel.classList.add("dragging-sheet");
      panel.style.transform = `translateY(${start.dy}px)`;
    }
  });
  const end = (e) => {
    if (!start || e.pointerId !== start.id) return;
    const dy = start.dy;
    start = null;
    panel.classList.remove("dragging-sheet");
    panel.style.transform = "";
    if (dy > 80) onClose();
  };
  panel.addEventListener("pointerup", end);
  panel.addEventListener("pointercancel", end);
}
