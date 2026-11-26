import { esc, int, popShort, compact } from "../format.js";
import { formatLensValue } from "./lenses.js";
import { glyph } from "./icon.js";
import { FOREIGN } from "../world.js";
import { t, placeName, terrainName, lensName } from "../i18n.js";

const el = () => document.getElementById("tooltip");

const nameOf = (table, id) => table.find((t) => t.id === id)?.name;

export function showCellTooltip(mx, my, w, i, lens, showResources = true) {
  const raw = w.raw;
  const lines = [];
  const city = w.cityByCell.get(i);
  if (city) lines.push(`<b>${esc(placeName(city))}</b> <span class="muted">· ${popShort(city.population)} ${t("people", "คน")}</span>`);

  const wt = w.water[i];
  if (wt) {
    const depth = raw.elev[i] < 0 ? ` <span class="muted">· ${t(`${int(-raw.elev[i])} m deep`, `ลึก ${int(-raw.elev[i])} ม.`)}</span>` : "";
    lines.push(`<b>${esc(terrainName(nameOf(w.tables.water, wt) || "Water"))}</b>${depth}`);
  } else {
    const cover = w.cover[i] > 0 ? terrainName(nameOf(w.tables.cover, w.cover[i])) : null;
    const relief = w.relief[i] > 0 ? terrainName(nameOf(w.tables.relief, w.relief[i])) : null;
    const terrain = [cover, relief].filter(Boolean).join(" · ") || (relief ?? t("Land", "แผ่นดิน"));
    lines.push(`<b>${esc(terrain)}</b> <span class="muted">· ${int(raw.elev[i])} ${t("m", "ม.")}</span>`);
  }
  const o = raw.owner[i];
  if (o >= 0) {
    const stObj = raw.states[o];
    const county = raw.county[i] >= 0 ? raw.counties[raw.county[i]].name + ", " : "";
    lines.push(`${esc(county)}${esc(placeName(stObj))}`);
    if (lens) lines.push(`${glyph(lens, 13)} ${esc(lensName(lens))}: <b>${formatLensValue(lens, lens.values[i])}</b>`);
  } else if (o === FOREIGN) {
    lines.push(`<span class="muted">${t("Beyond the borders (not mapped)", "นอกพรมแดนไทย (ไม่แสดงข้อมูล)")}</span>`);
  }
  const res = showResources && w.resources?.byCell.get(i);
  if (res) {
    for (const it of res.slice(0, 4)) {
      const tp = w.resources.typeById.get(it.type);
      const num = it.value == null ? "" : Math.abs(it.value) < 1e6 ? int(it.value) : compact(it.value);
      const val = num ? ` · ${num}${tp.unit ? " " + esc(tp.unit) : ""}` : "";
      const kind = it.name && it.name !== tp.name ? ` <span class="muted">· ${esc(tp.name)}${val}</span>` : `<span class="muted">${val}</span>`;
      lines.push(`<span style="color:${esc(tp.color || "#efe4c6")}">${glyph(tp, 13)}</span> ${esc(it.name || tp.name)}${kind}`);
    }
    if (res.length > 4) lines.push(`<span class="muted">+${res.length - 4} ${t("more", "รายการ")}</span>`);
  }
  if (city) lines.push(`<span class="muted">${t("Click to open the city", "คลิกเพื่อดูข้อมูลเมือง")}</span>`);
  else if (o >= 0) lines.push(`<span class="muted">${t(`Click to open ${raw.states[o].name}`, `คลิกเพื่อดูจังหวัด${placeName(raw.states[o])}`)}</span>`);
  show(mx, my, lines.join("<br>"));
}

/**
 * A tooltip with ready-made content: a string is HTML (escape any data yourself with format.js esc), {text} is
 * plain text. Used for registered static layers' tooltip(item).
 */
export function showHtmlTooltip(mx, my, content) {
  if (content == null || content === "") return hideTooltip();
  const html = typeof content === "string" ? content : esc(content.text ?? "");
  show(mx, my, html);
}

export function showCityTooltip(mx, my, city) {
  const title = placeName(city);
  const sub = city.th_name && title !== city.name ? ` (${city.name})` : (city.th_name && title === city.name ? ` (${city.th_name})` : "");
  show(mx, my, `<b>${esc(title)}</b><span class="muted">${esc(sub)}</span><br><span class="muted">${t("Click to open the city", "คลิกเพื่อเปิดหน้าเมือง")}</span>`);
}

function show(mx, my, html) {
  const t = el();
  t.innerHTML = html;
  t.hidden = false;
  const r = t.getBoundingClientRect();
  t.style.left = Math.max(4, Math.min(window.innerWidth - r.width - 8, mx + 16)) + "px";
  t.style.top = Math.max(4, Math.min(window.innerHeight - r.height - 8, my + 16)) + "px";
}

export function hideTooltip() {
  el().hidden = true;
}
