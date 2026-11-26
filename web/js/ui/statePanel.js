import { css } from "../color.js";
import { esc, popShort } from "../format.js";
import { isCapital } from "../world.js";
import { yieldGrid, amenities, industries, gdpRow, popLine, growthSpan, showPanel } from "./infoPanel.js";
import { t, isTh, placeName, regionName } from "../i18n.js";

/**
 * Opens the panel for state `idx` (index into world.json states / states.json).
 * ctx: {w, nation, states (states.json or null), cities, onClose, onPedia, onCity(city)}
 */
export function openStatePanel(idx, ctx) {
  const { w, nation } = ctx;
  const n = nation.nation;
  const geo = w.raw.states[idx] || {};
  // states.json is in the same order as world.json states; fall back to matching by fips.
  let st = ctx.states?.[idx];
  if (st && geo.fips && st.fips && st.fips !== geo.fips) st = ctx.states.find((s) => s.fips === geo.fips);
  st = st || { ...geo };
  const merged = { ...geo, ...st };
  const name = placeName(merged) || t("Province", "จังหวัด");
  const abbr = merged.abbr || "";
  const count = ctx.states?.length || w.raw.states.length;

  const cities = (ctx.cities || []).filter((c) => (c.states || []).includes(abbr)).slice(0, 8);
  const cityRows = cities.length
    ? `<div class="city-list">${cities
        .map((c) => {
          const multi = (c.states || []).length > 1 ? `<span class="muted"> · ${esc(c.states.join("–"))}</span>` : "";
          return `<button class="city-row" data-city="${esc(c.id)}" title="${esc(placeName(c))}">
            <span class="cr-name">${isCapital(c) ? "★ " : ""}${esc(placeName(c))}${multi}</span>
            <span class="cr-pop">${popShort(c.population)}</span><span class="cr-go" aria-hidden="true">›</span></button>`;
        })
        .join("")}</div>`
    : `<p class="muted">${t("No provincial hub in this province's data.", "ไม่มีข้อมูลเมืองหลักของจังหวัดนี้")}</p>`;

  const hasEcon = st.population != null || st.yields;
  const altName = isTh() ? merged.name : merged.th_name;
  const subParts = [altName, regionName(merged.region), abbr, geo.fips ? `DOPA ${geo.fips}` : ""].filter(Boolean);
  showPanel({
    kind: "state",
    stripe: css(w.stateColor[idx] || [190, 190, 190]),
    title: name,
    sub: esc(subParts.join(" · ")),
    headExtra: hasEcon ? popLine(st, growthSpan(st, n)) : "",
    sections: [
      st.yields && { title: t("Yields · rank among 77 provinces", "ผลผลิต · อันดับจาก 77 จังหวัด"), html: `<div class="yield-grid">${yieldGrid(nation, st.yields, st.ranks, count)}</div>` },
      hasEcon && { title: t("Living &amp; Economy", "ความเป็นอยู่และเศรษฐกิจ"), html: amenities(st, n) + gdpRow(st) },
      st.jobs && { title: t("Top sectors · GPP breakdown", "สาขาเศรษฐกิจหลัก · สัดส่วน GPP"), html: industries(st, nation, 8) },
      { title: t("Provincial hub (City View)", "เมืองหลักของจังหวัด (มุมมองเมือง)"), html: cityRows },
      !hasEcon && { title: t("Data", "ข้อมูล"), html: `<p class="muted">${t("Province statistics are not in this data build.", "ยังไม่มีข้อมูลสถิติของจังหวัดนี้")}</p>` },
    ],
    foot: `${t("Source", "แหล่งข้อมูล")}: ${esc(nation.vintage)}${nation.gdp_vintage ? `; GPP: ${esc(nation.gdp_vintage)}` : ""}. ${t(`Ranks are among all ${count} provinces of Thailand (1 = largest).`, `จัดอันดับจากทั้งหมด ${count} จังหวัดของประเทศไทย (อันดับ 1 = สูงสุด)`)}`,
    onClose: ctx.onClose,
    onPedia: ctx.onPedia,
    wire(panel) {
      panel.querySelectorAll("[data-city]").forEach((b) => {
        b.onclick = () => {
          const c = ctx.cities.find((x) => x.id === b.dataset.city);
          if (c) ctx.onCity(c);
        };
      });
    },
  });
}
