import { css } from "../color.js";
import { esc } from "../format.js";
import { isCapital } from "../world.js";
import { yieldGrid, amenities, industries, gdpRow, popLine, growthSpan, showPanel, hidePanel } from "./infoPanel.js";
import { t, isTh, placeName, regionName } from "../i18n.js";

/**
 * ctx: {w, nation, onClose, onPedia, onState(stateIndex)}
 */
export function openCityPanel(city, ctx) {
  const { w, nation } = ctx;
  const n = nation.nation;
  const owner = city.cell != null ? w.raw.owner[city.cell] : -1;
  const col = css(w.stateColor[owner] || [190, 190, 190]);

  // The city's states as links to their state panels.
  const states = (city.states || [])
    .map((abbr) => ({ abbr, i: w.raw.states.findIndex((s) => s.abbr === abbr) }))
    .map(({ abbr, i }) => (i >= 0 && ctx.onState
      ? `<button class="chip" data-state="${i}" title="${t("Open", "เปิด")} ${esc(placeName(w.raw.states[i]))}">${esc(abbr)}</button>`
      : `<span class="chip">${esc(abbr)}</span>`))
    .join("");

  const growth = growthSpan(city, n);
  const title = placeName(city);
  const subText = isTh()
    ? [city.name, regionName(city.region)].filter(Boolean).join(" · ")
    : (city.full || "");

  showPanel({
    kind: "city",
    stripe: col,
    title,
    titleHtml: `${isCapital(city) ? `<span class="cap" title="${t("National capital", "เมืองหลวง")}">★</span> ` : ""}${esc(title)}`,
    sub: `${esc(subText)}${states ? `<div class="chips">${states}</div>` : ""}`,
    headExtra: popLine(city, growth),
    sections: [
      { title: t("Yields (GPP by sector)", "ผลผลิตเศรษฐกิจ (GPP รายกลุ่มสาขา)"), html: `<div class="yield-grid">${yieldGrid(nation, city.yields)}</div>` },
      { title: t("Living &amp; Economy", "ความเป็นอยู่และเศรษฐกิจ"), html: amenities(city, n) + gdpRow(city) },
      { title: t("Districts · economic output by sector", "โครงสร้างเศรษฐกิจ · มูลค่า GPP รายสาขา"), html: industries(city, nation) },
    ],
    foot: `${t("Source", "แหล่งข้อมูล")}: ${esc(nation.vintage)}${nation.gdp_vintage ? `; GPP: ${esc(nation.gdp_vintage)}` : ""}.
      ${t("Green ×N = this sector's share of GPP is N× Thailand's national share.", "สีเขียว ×N = สัดส่วน GPP สาขานี้สูงกว่าค่าเฉลี่ยประเทศ N เท่า")}`,
    onClose: ctx.onClose,
    onPedia: ctx.onPedia,
    wire(panel) {
      panel.querySelectorAll("[data-state]").forEach((b) => (b.onclick = () => ctx.onState(+b.dataset.state)));
    },
  });
}

export const closeCityPanel = hidePanel;
