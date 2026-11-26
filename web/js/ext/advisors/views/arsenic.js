// Water & Arsenic advisor ("Guardian of Rivers" / "ผู้พิทักษ์สายน้ำ"):
// Visualizes Thailand's 2025–2026 transboundary arsenic crisis (Kok, Sai, Ruak, Mekong vs. Thai-origin
// control tributaries), the 2017–2025 Kok River baseline, and national arsenic watchpoints.
import { esc, fin, el as mk } from "../core/util.js";
import { barList } from "../core/charts.js";
import { createTable } from "../core/table.js";
import { section, tiles, segmented, mapPicker, sourcesHtml } from "../core/view.js";
import { frameBox, focusPoint, frameNation } from "../core/frame.js";
import { t, isTh, arsenicRiverLabel, arsenicWatchpoint } from "../../../i18n.js";

const STD_AS = 0.01;
const SEV_COLOR = { severe: "#e03838", exceed: "#e88a2e", safe: "#38a872" };

function fmtAs(v, digits = 3) {
  return fin(v) ? v.toFixed(digits) : "–";
}

function renderTrendSvg(rivers) {
  const W = 400, H = 175, PL = 42, PR = 14, PT = 14, PB = 28;
  const cw = W - PL - PR, ch = H - PT - PB;
  const maxY = 0.06;
  const xOf = (r) => PL + ((r - 1) / 7) * cw;
  const yOf = (v) => PT + ch - (Math.min(maxY, Math.max(0, v)) / maxY) * ch;

  const trans = rivers.filter((r) => r.transboundary);
  const ctrl = rivers.filter((r) => !r.transboundary);
  const ctrlPts = [];
  for (let rn = 1; rn <= 8; rn++) {
    const vals = ctrl.map((r) => r.by_round.find((x) => x.round === rn)?.mean_as).filter(fin);
    if (vals.length) ctrlPts.push({ round: rn, val: vals.reduce((a, b) => a + b, 0) / vals.length });
  }

  const lines = [
    ...trans.map((r) => ({
      id: r.id,
      label: arsenicRiverLabel(r),
      color: r.color,
      dashed: false,
      pts: r.by_round.filter((x) => fin(x.mean_as)).map((x) => ({ round: x.round, val: x.mean_as })),
    })),
    { id: "controls", label: t("Thai controls (<0.010)", "ลำน้ำควบคุมไทย (<0.010)"), color: "#38a872", dashed: true, pts: ctrlPts },
  ];

  const yTicks = [0, 0.01, 0.02, 0.04, 0.06];
  const gridSvg = yTicks.map((tv) => {
    const y = yOf(tv).toFixed(1);
    const isStd = Math.abs(tv - STD_AS) < 1e-6;
    return `<line x1="${PL}" y1="${y}" x2="${W - PR}" y2="${y}" stroke="${isStd ? "#ff6b6b" : "rgba(255,255,255,0.09)"}" stroke-width="${isStd ? 1.4 : 1}" ${isStd ? 'stroke-dasharray="4 3"' : ""}/>
      <text x="${PL - 6}" y="${(+y + 3).toFixed(1)}" text-anchor="end" font-size="9.5" fill="${isStd ? "#ff9b9b" : "#9c937c"}">${tv.toFixed(2)}</text>`;
  }).join("");

  const xTicks = [1, 2, 3, 4, 5, 6, 7, 8].map((r) =>
    `<text x="${xOf(r).toFixed(1)}" y="${H - 8}" text-anchor="middle" font-size="9.5" fill="#9c937c">${t(`R${r}`, `รอบ ${r}`)}</text>`
  ).join("");

  const paths = lines.map((ln) => {
    if (!ln.pts.length) return "";
    const d = ln.pts.map((p, i) => `${i ? "L" : "M"}${xOf(p.round).toFixed(1)},${yOf(p.val).toFixed(1)}`).join(" ");
    const dots = ln.pts.map((p) =>
      `<circle cx="${xOf(p.round).toFixed(1)}" cy="${yOf(p.val).toFixed(1)}" r="2.6" fill="${ln.color}"><title>${esc(ln.label)} ${t(`Round ${p.round}`, `รอบที่ ${p.round}`)}: ${p.val.toFixed(3)} ${t("mg/L", "มก./ล.")}</title></circle>`
    ).join("");
    return `<path d="${d}" fill="none" stroke="${ln.color}" stroke-width="2" ${ln.dashed ? 'stroke-dasharray="3 3"' : ""}/>${dots}`;
  }).join("");

  const stdY = yOf(STD_AS);
  const legend = lines.map((ln) =>
    `<span style="display:inline-flex;align-items:center;gap:4px;margin-right:10px;font-size:11px;color:#d6ccb2"><i style="display:inline-block;width:10px;height:3px;background:${ln.color};border-radius:1px"></i>${esc(ln.label)}</span>`
  ).join("");

  return `<svg viewBox="0 0 ${W} ${H}" style="width:100%;height:auto;display:block" role="img" aria-label="${t("Arsenic concentration by river across 8 monitoring rounds", "แนวโน้มค่าสารหนูรายลำน้ำ 8 รอบตรวจวัด")}">
    ${gridSvg}${xTicks}${paths}
    <text x="${W - PR}" y="${(stdY - 4).toFixed(1)}" text-anchor="end" font-size="9" fill="#ff9b9b">${t("Thai Std 0.010 mg/L", "มาตรฐานไทย 0.010 มก./ล.")}</text>
  </svg><div style="margin-top:4px;line-height:1.5">${legend}</div>`;
}

function renderBaselineSvg(baseline) {
  if (!baseline?.length) return `<p class="adv-note">${t("No historical baseline rows.", "ไม่มีข้อมูลฐานย้อนหลัง")}</p>`;
  const W = 400, H = 135, PL = 42, PR = 12, PT = 14, PB = 26;
  const cw = W - PL - PR, ch = H - PT - PB;
  const maxY = Math.max(0.05, ...baseline.map((b) => b.as_mg_l || 0));
  const bw = Math.max(5, (cw / baseline.length) - 3);
  const yOf = (v) => PT + ch - (Math.min(maxY, Math.max(0, v)) / maxY) * ch;
  const stdY = yOf(STD_AS);

  const bars = baseline.map((b, i) => {
    const x = PL + (i + 0.5) * (cw / baseline.length) - bw / 2;
    const h = Math.max(2, PT + ch - yOf(b.as_mg_l));
    const y = PT + ch - h;
    const col = b.as_mg_l > 0.03 ? "#e03838" : b.as_mg_l > STD_AS ? "#e88a2e" : "#4b9e76";
    const showYr = i === 0 || baseline[i - 1].year !== b.year;
    const yrLbl = isTh() ? String(b.year_be).slice(2) : String(b.year).slice(2);
    return `<rect x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${bw.toFixed(1)}" height="${h.toFixed(1)}" rx="1.5" fill="${col}">
      <title>${esc(b.date)} (พ.ศ. ${b.year_be} ${esc(b.month_th)}): ${b.as_mg_l.toFixed(3)} ${t("mg/L", "มก./ล.")}</title></rect>` +
      (showYr ? `<text x="${(x + bw / 2).toFixed(1)}" y="${H - 7}" text-anchor="middle" font-size="9" fill="#9c937c">${yrLbl}</text>` : "");
  }).join("");

  return `<svg viewBox="0 0 ${W} ${H}" style="width:100%;height:auto;display:block" role="img" aria-label="${t("Kok River historical arsenic baseline 2017 to 2025", "ข้อมูลฐานสารหนูแม่น้ำกก พ.ศ. 2560–2568")}">
    <line x1="${PL}" y1="${PT + ch}" x2="${W - PR}" y2="${PT + ch}" stroke="rgba(255,255,255,0.12)"/>
    <line x1="${PL}" y1="${stdY.toFixed(1)}" x2="${W - PR}" y2="${stdY.toFixed(1)}" stroke="#ff6b6b" stroke-width="1.3" stroke-dasharray="4 3"/>
    <text x="${PL - 6}" y="${(stdY + 3).toFixed(1)}" text-anchor="end" font-size="9" fill="#ff9b9b">0.01</text>
    <text x="${PL - 6}" y="${PT + 6}" text-anchor="end" font-size="9" fill="#9c937c">${maxY.toFixed(2)}</text>
    <text x="${PL - 6}" y="${PT + ch + 3}" text-anchor="end" font-size="9" fill="#9c937c">0.00</text>
    ${bars}
    <text x="${W - PR}" y="${(stdY - 4).toFixed(1)}" text-anchor="end" font-size="8.8" fill="#ff9b9b">${t("0.010 mg/L standard", "มาตรฐาน 0.010 มก./ล.")}</text>
  </svg>`;
}

export async function mount(ctx) {
  const { app, data, el, link } = ctx;
  const ars = await app.loadData("arsenic").catch(() => null);
  if (!ars) {
    el.innerHTML = `<p class="adv-empty pad">${t("arsenic.json is not built yet.", "ยังไม่ได้สร้างไฟล์ arsenic.json")}</p>`;
    return {};
  }

  // Ensure the Arsenic map layer is turned ON when opening this advisor
  app.ui?.setMapToggle?.("arsenic", true);

  const stations = ars.stations || [];
  const rivers = ars.rivers || [];
  const watchpoints = ars.watchpoints || [];
  const sum = ars.summary || {};

  // --- headline tiles -----------------------------------------------------------------------------------------
  const floodNote = (sum.pcd_flood_peak_note || "").replace(/\.$/, "");
  el.insertAdjacentHTML("beforeend", tiles([
    {
      label: t("Peak As (CSV)", "สารหนูสูงสุด (CSV)"),
      value: `${fmtAs(sum.peak_as_mg_l)}`,
      sub: t(
        `mg/L · ${(sum.peak_as_mg_l / STD_AS).toFixed(1)}× std (${sum.peak_station || ""})`,
        `มก./ล. · ${(sum.peak_as_mg_l / STD_AS).toFixed(1)}× มาตรฐาน (${sum.peak_station || ""})`
      ),
      color: "#ff7878",
    },
    {
      label: t("Exceeding sites", "สถานีเกินมาตรฐาน"),
      value: `${sum.exceeding_stations} / ${sum.total_stations}`,
      sub: t("100% of transboundary rivers", "100% ของแม่น้ำข้ามพรมแดน"),
      color: "#ffb65c",
    },
    {
      label: t("Thai controls", "ลำน้ำควบคุมไทย"),
      value: `${sum.control_exceeding} / ${sum.control_stations}`,
      sub: t("Lao, Suai, Korn (<0.010)", "แม่ลาว แม่สรวย แม่กรณ์ (<0.010)"),
      color: "#78dfa8",
    },
  ]) + `<p class="adv-callout">${t(
    `<b>Transboundary Northern Crisis (2025–2026):</b> Upstream gold &amp; rare-earth mining in Shan State, Myanmar has elevated Arsenic (As) across the <b>Sai, Kok, Ruak &amp; Mekong</b> rivers far above Thailand's <b>0.010 mg/L</b> standard${floodNote ? ` (${esc(floodNote)})` : ""}. Thai-origin control tributaries remain &lt;0.010 mg/L.`,
    `<b>วิกฤตสารหนูข้ามพรมแดนภาคเหนือ (2568–2569):</b> การทำเหมืองทองคำและแร่หายากต้นน้ำในรัฐฉาน เมียนมา ทำให้ค่าสารหนู (As) ใน<b>แม่น้ำสาย กก รวก และโขง</b> สูงเกินมาตรฐานไทย <b>0.010 มก./ล.</b> (คพ. รายงานช่วงน้ำหลากปี 2569 แม่น้ำสายพุ่งสูงสุดถึง 0.284 มก./ล. หรือ ~28× มาตรฐาน) ขณะที่ลำน้ำควบคุมที่ต้นน้ำอยู่ในไทยยังคง &lt;0.010 มก./ล.`
  )}</p>`);

  // --- quick framing + lens picker ----------------------------------------------------------------------------
  const mapRow = mk("div", "adv-sec adv-mapsec");
  el.appendChild(mapRow);
  const navRow = mk("div", "adv-row");
  navRow.innerHTML = `
    <button type="button" class="adv-mini" data-fly="basin">${t("Zoom to Kok &amp; Sai Basin", "ซูมไปลุ่มน้ำกก–สาย")}</button>
    <button type="button" class="adv-mini" data-fly="nation">${t("All Thailand", "ทั้งประเทศไทย")}</button>`;
  mapRow.appendChild(navRow);

  const flyBasin = () => {
    if (!stations.length) return;
    let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
    for (const s of stations) {
      x0 = Math.min(x0, s.x); x1 = Math.max(x1, s.x);
      y0 = Math.min(y0, s.y); y1 = Math.max(y1, s.y);
    }
    const pad = 16;
    frameBox(app, { x0: x0 - pad, y0: y0 - pad, x1: x1 + pad, y1: y1 + pad }, { pad: 24, maxScale: 6.0, ms: 500 });
  };
  navRow.addEventListener("click", (e) => {
    const act = e.target.closest("[data-fly]")?.dataset.fly;
    if (act === "basin") flyBasin();
    else if (act === "nation") frameNation(app);
  });

  if (app.lensById?.get("arsenic")) {
    mapPicker(ctx, mapRow, {
      label: t("Map", "แผนที่"),
      value: "terrain",
      options: [
        { value: "terrain", label: t("Terrain", "ภูมิประเทศ"), lens: () => null },
        { value: "arsenic", label: t("Arsenic (As)", "สารหนู (As)"), lens: () => "arsenic" },
        ...(app.lensById.get("disasters") ? [{ value: "disasters", label: t("Disasters", "ภัยพิบัติ"), lens: () => "disasters" }] : []),
      ],
    });
  }

  // --- river comparison ---------------------------------------------------------------------------------------
  const rBody = section(el, {
    title: t("Peak Arsenic by river", "ค่าสารหนูสูงสุดรายลำน้ำ"),
    kicker: t("Thai standard ≤ 0.010 mg/L", "มาตรฐานน้ำผิวดินไทย ≤ 0.010 มก./ล."),
    note: t(
      "Transboundary rivers from Shan State exceed 0.010 mg/L across all 20 stations; Thai-origin control tributaries stay below detection limit (&lt;0.010). Click a river to filter the station table.",
      "แม่น้ำข้ามพรมแดนจากรัฐฉานเกินมาตรฐาน 0.010 มก./ล. ครบทั้ง 20 สถานี ส่วนลำน้ำควบคุมที่ต้นน้ำอยู่ในไทยต่ำกว่าเกณฑ์ทั้งหมด (&lt;0.010) คลิกชื่อลำน้ำเพื่อกรองตารางสถานี"
    ),
  });
  let selectedRiver = "all";
  barList(rBody, {
    ariaLabel: t("Peak Arsenic by river", "ค่าสารหนูสูงสุดรายลำน้ำ"),
    rows: rivers.map((r) => ({
      key: r.id,
      label: arsenicRiverLabel(r),
      full: r.name,
      sub: t(
        `${r.exceeding_stations}/${r.stations} exceeding · ${r.exceed_samples}/${r.total_samples} rounds`,
        `เกิน ${r.exceeding_stations}/${r.stations} สถานี · ${r.exceed_samples}/${r.total_samples} รอบ`
      ),
      value: r.max_as,
      text: r.exceeding_stations === 0 && r.max_as <= 0.005
        ? t("<0.010 mg/L", "<0.010 มก./ล.")
        : `${fmtAs(r.max_as)} ${t("mg/L", "มก./ล.")}`,
      color: r.color,
    })),
    onHover: (row) => {
      if (!row) return link.hover(null);
      const cells = new Set(stations.filter((s) => s.river_id === row.key).map((s) => s.cell));
      link.hover({ cells, label: row.label });
    },
    onClick: (row) => {
      selectedRiver = selectedRiver === row.key ? "all" : row.key;
      applyFilter();
      const sts = stations.filter((s) => selectedRiver === "all" || s.river_id === selectedRiver);
      if (sts.length) {
        let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
        for (const s of sts) { x0 = Math.min(x0, s.x); x1 = Math.max(x1, s.x); y0 = Math.min(y0, s.y); y1 = Math.max(y1, s.y); }
        frameBox(app, { x0: x0 - 20, y0: y0 - 20, x1: x1 + 20, y1: y1 + 20 }, { pad: 24, maxScale: 5.5 });
      }
    },
  });

  // --- 8-round trend chart ------------------------------------------------------------------------------------
  const tSec = section(el, {
    title: t("8-round monitoring trend (2025–2026)", "แนวโน้มตรวจวัด 8 รอบ (2568–2569)"),
    kicker: t("Mean As (mg/L) per river", "ค่าเฉลี่ยสารหนู (มก./ล.) รายลำน้ำ"),
    note: t(
      "Every round across Sai, Kok, Mekong and Ruak compared with Thailand's 0.010 mg/L threshold (dashed red) and Thai control tributaries (dashed green).",
      "เปรียบเทียบค่าเฉลี่ยสารหนูทุกรอบของแม่น้ำสาย กก โขง และรวก กับเส้นมาตรฐานไทย 0.010 มก./ล. (เส้นประแดง) และลำน้ำควบคุมในไทย (เส้นประเขียว)"
    ),
  });
  tSec.insertAdjacentHTML("beforeend", renderTrendSvg(rivers));

  // --- historical baseline (2017–2025) ------------------------------------------------------------------------
  const bSec = section(el, {
    title: t("Historical baseline · Kok River (2017–2025)", "ข้อมูลฐานย้อนหลัง · แม่น้ำกก (พ.ศ. 2560–2568)"),
    kicker: t("Chiang Rai PHO (KK01)", "สสจ.เชียงราย (สถานี KK01)"),
    note: t(
      "Pre-crisis measurements (2017–2021) stayed at 0.000–0.003 mg/L before spiking to 0.025 mg/L (Dec 2022) and 0.044 mg/L (Aug 2024).",
      "ก่อนวิกฤต (พ.ศ. 2560–2564) ค่าสารหนูอยู่ที่ 0.000–0.003 มก./ล. ก่อนเริ่มพุ่งเป็น 0.025 มก./ล. (ธ.ค. 2565) และ 0.044 มก./ล. (ส.ค. 2567)"
    ),
  });
  bSec.insertAdjacentHTML("beforeend", renderBaselineSvg(ars.baseline));

  // --- station table ------------------------------------------------------------------------------------------
  const sSec = section(el, {
    title: t("Monitoring stations (23 sites)", "สถานีตรวจวัดคุณภาพน้ำ (23 จุด)"),
    note: t(
      "Hover a station to highlight its hex on the map; click to fly straight there.",
      "ชี้ชื่อสถานีเพื่อไฮไลต์ตำแหน่งบนแผนที่ หรือคลิกเพื่อซูมไปยังสถานีนั้นทันที"
    ),
  });
  let statusFilter = "all";
  const fRow = mk("div", "adv-row");
  sSec.appendChild(fRow);
  segmented(fRow, {
    label: t("Status", "สถานะ"),
    value: statusFilter,
    options: [
      { value: "all", label: t(`All (${stations.length})`, `ทั้งหมด (${stations.length})`) },
      { value: "exceed", label: t(`Exceeding (${sum.exceeding_stations})`, `เกินเกณฑ์ (${sum.exceeding_stations})`) },
      { value: "safe", label: t(`Safe Control (${sum.control_stations})`, `ปกติ/ควบคุม (${sum.control_stations})`) },
    ],
    onChange: (v) => { statusFilter = v; selectedRiver = "all"; applyFilter(); },
  });

  const tableHost = mk("div");
  sSec.appendChild(tableHost);
  const riverShortOf = (s) => {
    const r = rivers.find((x) => x.id === s.river_id);
    return isTh()
      ? arsenicRiverLabel(r).replace(" (ควบคุม)", "")
      : s.river_short.replace(" River", "").replace(" (Control)", "");
  };
  const table = createTable(tableHost, {
    caption: t("Arsenic monitoring stations", "ตารางสถานีตรวจวัดสารหนู"),
    rowKey: (s) => s.id,
    rowH: 30,
    maxHeight: 360,
    search: t("Search station ID, river, location", "ค้นหารหัสสถานี แม่น้ำ หรือพื้นที่"),
    searchText: (s) => `${s.id} ${s.name} ${s.location_th} ${s.river}`,
    columns: [
      {
        key: "id", label: t("Station", "สถานี"), align: "l", width: "minmax(0,2.1fr)",
        value: (s) => s.id,
        text: (s) => `${s.id} · ${isTh() ? (s.location_th || s.name) : s.name}`,
        html: (s) => `<b>${esc(s.id)}</b> <span style="color:#b9ab88;font-size:11px">${esc(isTh() ? (s.location_th || s.name) : s.name)}</span>`,
      },
      {
        key: "river_short", label: t("River", "ลำน้ำ"), align: "l", width: "74px",
        value: (s) => riverShortOf(s),
        text: (s) => riverShortOf(s),
      },
      {
        key: "max_as", label: t("Peak As", "สูงสุด"), align: "r", width: "62px",
        value: (s) => s.max_as,
        text: (s) => (s.exceed_rounds === 0 && s.max_as <= 0.005 ? "<0.010" : fmtAs(s.max_as)),
        html: (s) => `<span style="color:${SEV_COLOR[s.severity]};font-weight:600">${s.exceed_rounds === 0 && s.max_as <= 0.005 ? "&lt;0.010" : fmtAs(s.max_as)}</span>`,
      },
      {
        key: "ratio_max", label: t("× Std", "× เกณฑ์"), align: "r", width: "48px",
        value: (s) => s.ratio_max,
        html: (s) => (s.exceed_rounds > 0 ? `<b style="color:${SEV_COLOR[s.severity]}">${s.ratio_max}×</b>` : `<span style="color:#8f856b">&lt;1×</span>`),
      },
      {
        key: "exceed_rounds", label: t("Over", "เกิน"), align: "r", width: "44px",
        value: (s) => s.exceed_rounds,
        text: (s) => `${s.exceed_rounds}/${s.sampled_rounds}`,
      },
    ],
    sort: { key: "max_as", dir: "desc" },
    rows: stations,
    onHover: (s) => link.hover(s ? { cells: new Set([s.cell]), label: `${s.id} · ${s.exceed_rounds === 0 && s.max_as <= 0.005 ? "<0.010" : fmtAs(s.max_as)} ${t("mg/L", "มก./ล.")}` } : null),
    onClick: (s) => focusPoint(app, s.x, s.y, Math.min(app.cam.maxScale, Math.max(app.cam.scale, (app.cam.fitScale || 1) * 5.2))),
  });

  function applyFilter() {
    const filtered = stations.filter((s) => {
      if (selectedRiver !== "all" && s.river_id !== selectedRiver) return false;
      if (statusFilter === "exceed") return s.exceed_rounds > 0;
      if (statusFilter === "safe") return s.exceed_rounds === 0;
      return true;
    });
    table.setRows(filtered);
    const cells = new Set(filtered.map((s) => s.cell));
    link.set({ cells });
  }

  // --- national watchpoints -----------------------------------------------------------------------------------
  const wSec = section(el, {
    title: t("National watchpoints & historic hotspots", "จุดเฝ้าระวังระดับประเทศและพื้นที่ประวัติศาสตร์"),
    kicker: t("PCD · MOPH · DMR context", "บริบทจาก คพ. · สธ. · กรมทรัพยากรธรณี"),
    note: t(
      "Other documented arsenic zones in Thailand without a unified open-data CSV. Click any site to fly there on the map.",
      "พื้นที่ปนเปื้อนและจุดเฝ้าระวังสารหนูสำคัญอื่นในไทยที่ยังไม่มี CSV เปิดรวมชุดเดียว คลิกเพื่อบินไปยังตำแหน่งบนแผนที่"
    ),
  });
  const wpList = mk("div", "adv-cards");
  wpList.innerHTML = watchpoints.map((rawWp) => {
    const wp = arsenicWatchpoint(rawWp);
    return `
    <button type="button" class="city-row" data-wp="${esc(wp.id)}" style="display:block;width:100%;text-align:left;padding:8px 10px;margin-bottom:6px;border-radius:6px;background:rgba(160,110,224,0.1);border:1px solid rgba(160,110,224,0.3);color:#efe4c6;cursor:pointer">
      <div style="display:flex;justify-content:space-between;gap:8px;align-items:baseline">
        <b>◆ ${esc(wp.name)}</b><span style="font-size:11px;color:#c9a8ff">${esc(wp.province)}</span>
      </div>
      <div style="font-size:11px;color:#b9ab88;margin-top:2px">${esc(isTh() ? rawWp.name : rawWp.th_name)} · ${esc(wp.status)}</div>
      <div style="font-size:11.5px;color:#d6ccb2;margin-top:4px;line-height:1.35">${esc(wp.summary)}</div>
    </button>`;
  }).join("");
  wSec.appendChild(wpList);
  wpList.addEventListener("click", (e) => {
    const id = e.target.closest("[data-wp]")?.dataset.wp;
    const rawWp = watchpoints.find((x) => x.id === id);
    if (rawWp) {
      const wp = arsenicWatchpoint(rawWp);
      link.hover({ cells: new Set([rawWp.cell]), label: wp.name });
      focusPoint(app, rawWp.x, rawWp.y, Math.min(app.cam.maxScale, Math.max(app.cam.scale, (app.cam.fitScale || 1) * 4.0)));
    }
  });

  // --- caution, methodology & validation references -----------------------------------------------------------
  const foot = section(el, { title: t("Caution to use & validation references", "ข้อควรระวังการใช้งานและแหล่งอ้างอิงตรวจสอบ") });
  foot.insertAdjacentHTML("beforeend", `
    <div class="adv-caution">
      <b>⚠ ${t("Caution — Not a live water-safety advisory", "ข้อควรระวัง — ไม่ใช่ประกาศความปลอดภัยน้ำดื่มแบบเรียลไทม์")}:</b>
      <ul>
        <li>${t(
          "This dashboard visualizes official historical/multi-round CSV snapshots for public awareness and research only. Do <b>not</b> rely on it for drinking, cooking, agricultural, or medical decisions.",
          "แดชบอร์ดนี้แสดงข้อมูลจากไฟล์ CSV ทางการย้อนหลังและรายรอบเพื่อการรับรู้และศึกษาเท่านั้น <b>ห้ามใช้ประกอบการตัดสินใจด้านการบริโภคน้ำ การเกษตร หรือการแพทย์</b>"
        )}</li>
        <li>${t(
          "Provinces without monitoring CSVs appear as <b>no data</b> — this does <b>not</b> mean safe. Always follow live advisories from PCD, Provincial Waterworks Authority (PWA), and Chiang Rai PHO.",
          "จังหวัดที่ไม่มีชุดข้อมูลตรวจวัดจะแสดงเป็น <b>ไม่มีข้อมูล</b> ซึ่ง<b>ไม่ได้หมายความว่าปลอดภัย</b> โปรดติดตามประกาศล่าสุดจาก คพ., กปภ. และ สสจ.เชียงราย โดยตรง"
        )}</li>
      </ul>
    </div>
    <p class="adv-note">${esc(t(
      ars.caveats || "",
      "ค่าตรวจวัด 23 สถานีมาจากชุดข้อมูลเปิดทางการของจังหวัดเชียงราย (chiangrai.gdcatalog.go.th / คพ.) โดยค่า '0' ในไฟล์ CSV หมายถึงไม่ได้เก็บตัวอย่างในรอบนั้น (ไม่ถูกนับเป็นค่าศูนย์จริง) และค่า '<0.010' คือต่ำกว่าขีดจำกัดการตรวจวัด (พล็อตในกราฟแนวโน้มที่ 0.005 มก./ล. และนับว่าผ่านเกณฑ์) เลนส์สารหนูระบายสีเฉพาะ Hex ที่มีสถานีตรวจวัดจริงเท่านั้น ไม่มีการประมาณค่าข้ามจังหวัด"
    ))}</p>
    <ul class="adv-refs">
      <li><a href="https://chiangrai.gdcatalog.go.th/dataset/e1fc8a4f-1d5c-4571-aff2-89a35e554a08" target="_blank" rel="noopener noreferrer">${t("Chiang Rai Open Data — 23-Station × 8-Round Arsenic Monitoring CSV ↗", "บัญชีข้อมูลเปิดเชียงราย — CSV ตรวจวัดสารหนู 23 สถานี × 8 รอบ ↗")}</a></li>
      <li><a href="https://chiangrai.gdcatalog.go.th/dataset/2e5aa282-25db-460c-ac6d-d38c4e1bf468" target="_blank" rel="noopener noreferrer">${t("Chiang Rai Open Data — Kok River 2017–2025 Historical Baseline CSV ↗", "บัญชีข้อมูลเปิดเชียงราย — CSV ข้อมูลฐานแม่น้ำกก พ.ศ. 2560–2568 ↗")}</a></li>
      <li><a href="https://www.pcd.go.th/" target="_blank" rel="noopener noreferrer">${t("Pollution Control Department (PCD) — Official Live Advisories &amp; 0.010 mg/L Standard ↗", "กรมควบคุมมลพิษ (คพ.) — ประกาศสถานการณ์ล่าสุดและมาตรฐาน 0.010 มก./ล. ↗")}</a></li>
      <li><button type="button" class="adv-link" data-pedia="Caution & Validation">${t("Full Caution, Limitations &amp; SHA-256 Checksums in the Almanac ›", "อ่านข้อควรระวังฉบับเต็มและรหัสตรวจสอบ SHA-256 ในสารานุกรม ›")}</button></li>
    </ul>`);
  el.insertAdjacentHTML("beforeend", sourcesHtml(data, ["arsenic_thailand"]));

  // If opened via clicking a specific station or watchpoint, zoom right to it; otherwise frame the Kok-Sai basin!
  const targetId = ctx.params?.station;
  const hitSt = stations.find((s) => s.id === targetId);
  const hitWp = watchpoints.find((w) => w.id === targetId);
  if (hitSt) {
    focusPoint(app, hitSt.x, hitSt.y, Math.min(app.cam.maxScale, (app.cam.fitScale || 1) * 5.2));
    link.hover({ cells: new Set([hitSt.cell]), label: `${hitSt.id} · ${fmtAs(hitSt.max_as)} ${t("mg/L", "มก./ล.")}` });
  } else if (hitWp) {
    focusPoint(app, hitWp.x, hitWp.y, Math.min(app.cam.maxScale, (app.cam.fitScale || 1) * 4.0));
  } else {
    flyBasin();
  }

  return {
    destroy() {
      link.clear();
    },
  };
}
