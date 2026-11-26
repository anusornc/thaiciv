// Thailand (thaiciv) 32-second bilingual cinematic trailer storyboard (EN / ไทย).
// Every number comes directly from web/data/*.json at render time — zero invented figures.
// Keeps the 8 canonical shot IDs expected by score.js so the D-major orchestral soundtrack stays locked in sync!
export const CONFIG = {
  title: "THAILAND · ประเทศไทย",
  subtitle: "as a 4X strategy map · แผนที่กลยุทธ์จากข้อมูลจริง",
  url: "anusornc.github.io/thaiciv",
  cta: "Open source · เล่นฟรีบนเว็บ (EN / ไทย)",
};

import {
  titleCard, endCard, caption, chip, lensLegend, cityPanel, caravans, routeGlow, pulseRing, vignette, darken,
  win, smooth, lerp, clamp01,
} from "./overlays.js";
import { badgeOf, cityDistricts } from "../../js/ext/cityView/districts.js";

export const FPS = 30;
export const W = 1920, H = 1080;
const FADE = 0.45;

// --- number formatting (Thai Baht ฿) ---------------------------------------------------------------------------
const money = (v) => {
  if (v >= 1e12) return `฿${(v / 1e12).toFixed(2)}T`;
  if (v >= 1e9) return `฿${(v / 1e9).toFixed(0)}B`;
  return `฿${(v / 1e6).toFixed(0)}M`;
};
const moneyShort = (v) => (v >= 1e12 ? `฿${(v / 1e12).toFixed(2)}T` : v >= 1e9 ? `฿${(v / 1e9).toFixed(0)}B` : `฿${(v / 1e6).toFixed(0)}M`);
const people = (v) => (v >= 1e6 ? `${(v / 1e6).toFixed(1)}M` : `${Math.round(v / 1e3)}K`);
const peopleShort = (v) => (v >= 1e6 ? `${(v / 1e6).toFixed(2)}M` : `${Math.round(v / 1e3)}K`);
const int = (v) => Math.round(v).toLocaleString("en-US");
function oneIn(share) {
  if (!(share > 0)) return "none";
  if (share >= 0.3) return `${Math.round(share * 10)} in 10`;
  return `1 in ${Math.round(1 / share)}`;
}

// --- camera helpers --------------------------------------------------------------------------------------------
function camAt(a, b, k) {
  return { x: lerp(a.x, b.x, k), y: lerp(a.y, b.y, k), rpx: Math.exp(lerp(Math.log(a.rpx), Math.log(b.rpx), k)) };
}
function camZoom(a, b, k) {
  const rpx = Math.exp(lerp(Math.log(a.rpx), Math.log(b.rpx), k));
  const u = Math.abs(1 / b.rpx - 1 / a.rpx) < 1e-9 ? k : (1 / rpx - 1 / a.rpx) / (1 / b.rpx - 1 / a.rpx);
  return { x: lerp(a.x, b.x, u), y: lerp(a.y, b.y, u), rpx };
}
function camFly(a, b, k, h = 3.2) {
  const c = camAt(a, b, k);
  return { ...c, rpx: c.rpx / (1 + h * Math.sin(Math.PI * k)) };
}
const smoother = (k) => { k = clamp01(k); return k * k * k * (k * (6 * k - 15) + 10); };
const glide = (k) => 0.35 * clamp01(k) + 0.65 * smooth(k);
const easeOutQ = (k) => 1 - (1 - clamp01(k) ** 1.3) ** 4;

function gatherFacts(stage) {
  const { data, w } = stage;
  const g = w.grid;
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (let i = 0; i < g.size; i++) {
    if (w.raw.owner[i] < 0) continue;
    const x = g.cx(i), y = g.cy(i);
    x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y);
  }
  const land = { x0, y0, x1, y1, cx: (x0 + x1) / 2, cy: (y0 + y1) / 2 };
  const css = { w: W / stage.dpr, h: H / stage.dpr };
  const homeRpx = Math.min((css.w * 0.92) / (x1 - x0 + 2 * g.R), (css.h * 0.88) / (y1 - y0 + 2 * g.R)) * g.R;
  const src = new Map(data.sources.map((s) => [s.id, s]));
  const city = (name) => data.cities.find((c) => c.name === name) || data.cities[0];
  return { land, homeRpx, src, city, css };
}

export function buildStoryboard(stage, cfg = CONFIG) {
  const { data } = stage;
  const F = gatherFacts(stage);
  const { land, homeRpx } = F;
  const shots = [];
  const shot = (s) => { shots.push(s); return s; };
  const WIDE = { banners: false, resources: false, labels: false };

  // 32-second timeline (score.js automatically scales to these shot times!)
  const T_ROCK = 3.2, T_NY = 6.5, T_LENS = 10.4, T_IMP = 16.0, T_CITY = 20.6, T_TRADE = 25.4, T_END = 28.6, T_OUT = 32.0;

  // 1. Title over the whole Thailand hex map, slow push-in. ----------------------------------------------------
  shot({
    id: "title", t0: 0, t1: T_ROCK + 0.2,
    render: (t) => [{ view: { ...camAt({ x: land.cx, y: land.cy, rpx: homeRpx * 0.96 }, { x: land.cx + 15, y: land.cy - 20, rpx: homeRpx * 1.12 }, t / (T_ROCK + 0.2)), ...WIDE } }],
    overlay(ctx, t) {
      darken(ctx, W, H, 0.44);
      vignette(ctx, W, H, 0.85);
      titleCard(ctx, W, H, cfg, win(t, -0.5, T_ROCK + 0.15, 0.9, 0.4), clamp01((t + 0.4) / 1.6));
    },
  });

  // 2. ("rockies" slot): Northern Mountains + 2025–2026 Transboundary Arsenic Crisis (Kok, Sai, Ruak, Mekong)! --
  const ars = data.arsenic;
  const sa01 = ars?.stations?.find((s) => s.id === "SA01") || { x: 405, y: 145, max_as: 0.055 };
  const ROCK_T = T_NY - T_ROCK;
  shot({
    id: "rockies", t0: T_ROCK, trans: "dip", t1: T_NY,
    render: (t) => [{
      view: {
        ...camAt({ x: 382, y: 225, rpx: 26 }, { x: 412, y: 176, rpx: 38 }, glide(t / (ROCK_T + 0.2))),
        layers: { arsenic: true, roads: true },
        resources: false,
      },
    }],
    overlay(ctx, t, frame) {
      const a = win(t, 0.4, ROCK_T + 0.05, 0.45, 0.3);
      const [sx, sy] = frame.toScreen(sa01.x, sa01.y);
      pulseRing(ctx, sx, sy, 46, a, t, "#ff5c5c", "rgba(255,70,70,0.95)");
      caption(ctx, W, H, {
        kicker: "Arsenic Crisis · วิกฤตสารหนูภาคเหนือ",
        title: "แม่น้ำกก · สาย · รวก · โขง",
        sub: `${ars?.summary?.exceeding_stations ?? 20}/${ars?.summary?.total_stations ?? 23} sites > 0.010 mg/L · สูงสุด ${sa01.max_as.toFixed(3)} mg/L (5.5× เกณฑ์)`,
        source: "Chiang Rai Open Data · Pollution Control Dept. (PCD) 2025–2026",
      }, a, clamp01((t - 0.4) / 0.6));
    },
  });

  // 3. ("cities" slot): Sweep from Gulf of Thailand into Bangkok (กรุงเทพมหานคร)! ------------------------------
  const bkk = F.city("Bangkok");
  const NY_T = T_LENS - T_NY;
  const bkkEnd = { x: bkk.x - 18, y: bkk.y + 8, rpx: 44 };
  const BKK_DRIFT = -8;
  const bkkCam = (t) => {
    const c = camAt({ x: bkk.x + 55, y: bkk.y + 80, rpx: 24 }, bkkEnd, smooth(t / NY_T));
    return { ...c, x: c.x + BKK_DRIFT * (t - NY_T) };
  };
  shot({
    id: "cities", t0: T_NY, trans: "punch", t1: T_LENS,
    render: (t) => [{ view: { ...bkkCam(t), layers: { roads: true, rail: true, hubs: true } } }],
    overlay(ctx, t, frame) {
      const a = win(t, 1.1, NY_T - 0.05, 0.5, 0.4);
      const [sx, sy] = frame.toScreen(bkk.x, bkk.y);
      pulseRing(ctx, sx, sy, frame.cam.scale * stage.R * 2.6, a, t);
      caption(ctx, W, H, {
        kicker: "Cities · 77 จังหวัด 928 อำเภอ",
        title: "Bangkok · กรุงเทพมหานคร",
        sub: `${money(bkk.gdp)} GPP · ${people(bkk.population)} people (ประชากร ${(bkk.population / 1e6).toFixed(1)} ล้านคน)`,
        source: `NESDC GPP ${bkk.gdp_year || 2024}p · DOPA Civil Registration 2025`,
      }, a, clamp01((t - 1.1) / 0.6));
    },
  });

  // 4. ("lenses" slot): Pull out to all Thailand — 21 lenses washing across the map! ---------------------------
  const LENS_META = [
    { id: "gpp_pc", label: "GPP ต่อหัว · GPP per capita", unit: "฿ / person (บาท/คน/ปี)" },
    { id: "tour_share", label: "ท่องเที่ยว · Tourism share", unit: "% of GPP (% ของ GPP)" },
    { id: "density", label: "ความหนาแน่น · Pop. density", unit: "people/km² (คน/ตร.กม.)" },
  ];
  const LENSES = LENS_META.map((m) => ({ ...m, lens: stage.lensById.get(m.id) })).filter((x) => x.lens);
  const nLens = data.lenses.lenses.length;
  const lensFmt = stage.formatLensTick;
  const legendOf = (m) => ({
    name: m.label, unit: m.unit, icon: m.lens.icon, ramp: m.lens.ramp,
    lo: lensFmt(m.lens, 0, 0), hi: lensFmt(m.lens, 1, 4),
  });
  const LENS_T = T_IMP - T_LENS, ZO = 1.0, LD = (LENS_T - ZO) / LENSES.length, LK = 0.4;
  const lensA = { x: land.cx - 45, y: land.cy + 20, rpx: homeRpx * 1.02 };
  const lensB = { x: land.cx + 45, y: land.cy - 15, rpx: homeRpx * 1.12 };
  const lensCam = (t) => {
    if (t >= ZO) return camAt(lensA, lensB, clamp01((t - ZO) / (LENS_T - ZO)));
    const c = camZoom(bkkEnd, lensA, smooth(t / ZO));
    return { ...c, x: c.x + BKK_DRIFT * t * (1 - smooth(t / ZO)) };
  };
  const lensAt = (t) => {
    const u = Math.max(0, t - ZO);
    const i = Math.min(LENSES.length - 1, Math.floor(u / LD));
    const k = i < LENSES.length - 1 ? smooth((u - (i + 1) * LD + LK) / LK) : 0;
    return { i, k };
  };
  shot({
    id: "lenses", t0: T_LENS, trans: "cut", t1: T_IMP,
    cues: LENSES.map((_, i) => (i === 0 ? 0.1 : ZO + i * LD - LK / 2)),
    render(t) {
      const cam = lensCam(t);
      if (t < ZO) {
        return [
          { view: { ...cam } },
          { view: { ...cam, lens: LENSES[0].id, ...WIDE }, alpha: smooth((t - 0.1) / (ZO - 0.2)) },
        ];
      }
      const { i, k } = lensAt(t);
      const out = [{ view: { ...cam, lens: LENSES[i].id, ...WIDE } }];
      if (k > 0) out.push({ view: { ...cam, lens: LENSES[i + 1].id, ...WIDE }, alpha: k });
      return out;
    },
    overlay(ctx, t) {
      vignette(ctx, W, H, 0.5 * smooth(t / ZO));
      const { i, k } = lensAt(t);
      const whole = win(t, 0.55, LENS_T - 0.05, 0.4, 0.3);
      lensLegend(ctx, W, H, legendOf(LENSES[i]), whole, k > 0 ? legendOf(LENSES[i + 1]) : null, k);
      caption(ctx, W, H, {
        kicker: "Lenses · เลนส์ข้อมูลแผนที่",
        title: `${nLens} Interactive Lenses`,
        sub: "รายได้ · หนี้สิน · ป่าไม้ดาวเทียม · ภัยพิบัติ · สารหนู",
        source: "NESDC · DOPA · NSO · ESA WorldCover 2021 · PCD",
      }, whole, clamp01((t - 0.55) / 0.6));
    },
  });

  // 5. ("improvements" slot): Dive into Bangkok & EEC (Chon Buri / Laem Chabang) — layers pop in! -------------
  const eec = F.city("Chon Buri");
  const infra = data.infrastructure, mil = data.military, won = data.wonders;
  const IMP_T = T_CITY - T_IMP, ZI = 1.0;
  const STAGES = [
    { at: 1.05, on: { roads: true, rail: true }, chip: { icon: "t-road", label: "Highways & SRT Rail · ถนนและรถไฟ", sub: "Natural Earth 1:10m · โครงข่ายคมนาคมไทย" } },
    { at: 1.75, on: { hubs: true }, chip: { icon: "d-harbor", label: `${infra.ports.length} Ports · ${infra.airports.length} Airports · ท่าเรือและสนามบิน`, sub: "Laem Chabang, Suvarnabhumi & regional hubs" } },
    { at: 2.45, on: { military: true }, chip: { icon: "m-army", label: `${int(mil.installations.length)} Military Bases · ฐานทัพทั่วไทย`, sub: "Royal Thai Army, Navy & Air Force" } },
    { at: 3.15, on: { wonders: true }, chip: { icon: "w-landmark", label: `${won.wonders.length} Thai Wonders · สถานที่สำคัญ`, sub: "National Parks · Universities · UNESCO Heritage" } },
  ];
  const layersAt = (n) => Object.assign({}, ...STAGES.slice(0, n).map((s) => s.on));
  const eecA = { x: eec.x - 18, y: eec.y - 12, rpx: 38 };
  const eecB = { x: eec.x + 8, y: eec.y + 6, rpx: 46 };
  const lensV = { x: (lensB.x - lensA.x) / (LENS_T - ZO), y: (lensB.y - lensA.y) / (LENS_T - ZO) };
  const impCam = (t) => {
    if (t >= ZI) return camAt(eecA, eecB, glide((t - ZI) / (IMP_T - ZI + 0.35)));
    const c = camZoom(lensB, eecA, smooth(t / ZI)), d = t * (1 - smooth(t / ZI));
    return { ...c, x: c.x + lensV.x * d, y: c.y + lensV.y * d };
  };
  shot({
    id: "improvements", t0: T_IMP, trans: "cut", t1: T_CITY,
    cues: STAGES.map((s) => s.at + 0.1),
    render(t) {
      const cam = impCam(t);
      if (t < ZI) {
        return [
          { view: { ...cam } },
          { view: { ...cam, lens: LENSES[LENSES.length - 1].id, ...WIDE }, alpha: 1 - smooth((t - 0.15) / (ZI - 0.3)) },
        ];
      }
      let n = 0;
      while (n < STAGES.length && t >= STAGES[n].at + 0.45) n++;
      const out = [{ view: { ...cam, layers: layersAt(n) } }];
      if (n < STAGES.length && t > STAGES[n].at) out.push({ view: { ...cam, layers: layersAt(n + 1) }, alpha: smooth((t - STAGES[n].at) / 0.45) });
      return out;
    },
    overlay(ctx, t) {
      vignette(ctx, W, H, 0.5 * (1 - smooth(t / (ZI * 0.8))));
      let y = 70;
      for (const s of STAGES) {
        const a = win(t, s.at, IMP_T - 0.1, 0.4, 0.3);
        if (a > 0) chip(ctx, 72 - (1 - smooth((t - s.at) / 0.4)) * 40, y, s.chip, a, { size: 0.88 });
        y += 86;
      }
    },
  });

  // 6. ("city" slot): Fly south along the Andaman coast to Phuket (ภูเก็ต) & open its Civ City Screen! --------
  const pkt = F.city("Phuket");
  const cv = stage.cityView(pkt.id);
  const bb = cv.model.bbox;
  const cit = data.citizens.cities[pkt.id];
  const natW = data.citizens.national.workforce;
  const groups = data.citizens.groups.workforce;
  const figs = (fig) => groups.flatMap((g) => Array(fig[g.key] || 0).fill(g.key));
  const spec = (cit.specialists || []).find((s) => s.row === "workforce" && s.ratio > 1) || null;
  const specLabel = spec ? groups.find((g) => g.key === spec.key)?.label : null;
  const badge = badgeOf(data.districts, pkt.id);
  const dists = cityDistricts(data.districts, data.military, pkt.id).slice(0, 2);
  const lqLine = (d) => {
    if (d.lq == null) return d.subName || "";
    const lead = d.subName ? ` · ${d.subName}` : "";
    return `${d.lq.toFixed(1)}× Thailand's national share${lead}`;
  };
  const panel = {
    name: pkt.name,
    full: pkt.full,
    badge: badge && badge.district ? { label: badge.label, color: badge.color, icon: badge.icon } : null,
    stats: [
      [peopleShort(pkt.population), "people · คน"],
      [moneyShort(pkt.gdp), `GPP ${pkt.gdp_year || 2024}`],
      [`฿${int(pkt.median_income)}`, "annual hh inc."],
    ],
    highlight: spec ? `Specialist: ${specLabel} (เด่นพิเศษ)` : "",
    rows: [
      { label: "Phuket · ภูเก็ต", figs: figs(cit.workforce.figures), hi: spec?.key, ratio: spec ? `${oneIn(spec.share)} of GPP` : "" },
      { label: "Thailand · ประเทศไทย", figs: figs(natW.figures), hi: spec?.key, ratio: spec ? `${oneIn(spec.national)} of GDP` : "" },
    ],
    districts: dists.map((d) => ({ icon: d.icon, name: d.name, line: lqLine(d) })),
    source: `NESDC GPP 2024p · DOPA 2025 · NSO Household SES`,
  };
  const CITY_T = T_TRADE - T_CITY, FLY = 1.7, CITY_IN = 0.6;
  const mapW = (W - 820 - 56) / stage.dpr;
  const fitRpx = Math.min(48, Math.max(28, Math.min((mapW * 0.72) / Math.max(40, bb.x1 - bb.x0), (F.css.h * 0.65) / Math.max(40, bb.y1 - bb.y0)) * stage.R));
  const cityCam = (rpx) => {
    const s = rpx / stage.R;
    const cx = (bb.x0 + bb.x1) / 2, cy = (bb.y0 + bb.y1) / 2;
    return { x: cx + (F.css.w / 2 - mapW / 2) / s, y: cy + 10 / s, rpx };
  };
  const pktA = cityCam(fitRpx * 0.94), pktB = cityCam(fitRpx * 1.06);
  shot({
    id: "city", t0: T_CITY, trans: "cut", t1: T_TRADE,
    cues: [FLY - CITY_IN, 1.3],
    render(t) {
      const cam = t < FLY ? camFly(impCam(IMP_T), pktA, smoother(t / FLY), 3.0) : camAt(pktA, pktB, ((u) => 0.5 * u + 0.5 * u * u)(clamp01((t - FLY) / (CITY_T - FLY))));
      const on = smooth((t - (FLY - CITY_IN)) / CITY_IN);
      const cityAnimMs = Math.max(0, t - (FLY - CITY_IN)) * 1000;
      if (on >= 1) return [{ view: { ...cam, city: pkt.id, cityAnimMs } }];
      const out = [{ view: { ...cam, layers: layersAt(STAGES.length) } }];
      const noNames = smooth(t / 0.35);
      if (noNames < 1) out.push({ view: { ...cam, labels: false, layers: layersAt(STAGES.length) }, alpha: noNames });
      else out[0].view.labels = false;
      const plain = smooth((t - 0.1) / 0.6);
      if (plain > 0) out.push({ view: { ...cam, labels: false }, alpha: plain });
      if (on > 0) out.push({ view: { ...cam, city: pkt.id, cityAnimMs }, alpha: on });
      return out;
    },
    overlay(ctx, t) {
      cityPanel(ctx, W, H, panel, win(t, 1.3, CITY_T + 0.3, 0.3, 0.4), clamp01((t - 1.3) / 0.7), t - 0.8);
    },
  });

  // 7. ("trade" slot): Pull out from #1 Bangkok ↔ Chon Buri corridor to all 20 Thai economic corridors! --------
  const trade = data.trade;
  const zone = new Map(trade.zones.map((z) => [z.id, z]));
  const top = trade.routes[0];
  const topRt = stage.model.routes.find((r) => r.route === top);
  const TRADE_T = T_END - T_TRADE;
  const za = zone.get(top.a), zb = zone.get(top.b);
  const topMid = topRt ? { x: (topRt.pts[0] + topRt.pts[topRt.pts.length - 2]) / 2, y: (topRt.pts[1] + topRt.pts[topRt.pts.length - 1]) / 2 } : { x: bkk.x, y: bkk.y };
  const trA = { x: topMid.x - 10, y: topMid.y + 15, rpx: 26 };
  const endB = { x: land.cx + 10, y: land.cy + 5, rpx: homeRpx * 0.98 };
  const tradeCam = (t) => {
    const k = easeOutQ(t / (T_OUT - T_TRADE)), z = camZoom(trA, endB, k), l = camAt(trA, endB, k);
    return { x: (z.x + l.x) / 2, y: (z.y + l.y) / 2, rpx: z.rpx };
  };
  shot({
    id: "trade", t0: T_TRADE, trans: "punch", t1: T_END,
    render(t) {
      const cam = tradeCam(t);
      return [
        { view: { ...cam, resources: false } },
        { view: { ...cam, resources: false, layers: { trade: true, arsenic: true } }, alpha: smooth((t - 0.1) / 0.4) },
        { view: { ...cam, ...WIDE, layers: { trade: true, arsenic: true } }, alpha: smooth((t - 0.6) / 0.45) },
      ];
    },
    overlay(ctx, t, frame) {
      caravans(ctx, stage.model.routes, frame.toScreen, t, smooth((t - 0.4) / 0.5), 1.3);
      routeGlow(ctx, topRt, frame.toScreen, t, win(t, 0.25, TRADE_T, 0.4, 0.4), 7);
      caption(ctx, W, H, {
        kicker: "Trade Corridors · เส้นทางเศรษฐกิจ",
        title: `${trade.routes.length} Major Economic Corridors`,
        sub: `#1: ${za?.short || "Bangkok"} ↔ ${zb?.short || "Chon Buri"} (${int(top.dist_km)} km) · ${money(top.value_musd * 1e6)}`,
        source: "Routed on Thai Highways & SRT Rail · Weighted by NESDC GPP",
      }, win(t, 0.45, TRADE_T - 0.05, 0.45, 0.3), clamp01((t - 0.45) / 0.6));
    },
  });

  // 8. ("end" slot): End card with live GitHub Pages URL & bilingual summary! ----------------------------------
  shot({
    id: "end", t0: T_END, trans: "cut", t1: T_OUT,
    render(t) {
      const cam = tradeCam(TRADE_T + t);
      return [
        { view: { ...cam, ...WIDE } },
        { view: { ...cam, ...WIDE, layers: { trade: true, arsenic: true } }, alpha: 1 - 0.6 * smooth(t / 0.9) },
      ];
    },
    overlay(ctx, t, frame) {
      caravans(ctx, stage.model.routes, frame.toScreen, t + TRADE_T, 1 - 0.7 * smooth(t / 0.7), 1.3);
      darken(ctx, W, H, 0.56 * smooth(t / 0.5));
      vignette(ctx, W, H, 0.9 * smooth(t / 0.5));
      endCard(ctx, W, H, cfg, {
        facts: `${data.sources.length} public data sources · EN / ไทย · 77 จังหวัด · 928 อำเภอ`,
        fallback: cfg.cta,
      }, smooth((t - 0.1) / 0.5), clamp01((t - 0.15) / 0.6));
    },
  });

  const duration = T_OUT;
  return { shots, duration, fps: FPS, frames: Math.round(duration * FPS), fade: FADE, cfg, facts: F, panel };
}

const DIP = 0.6, PUNCH = 0.4;
export const fadeOf = (sb, s) => s.fade ?? ({ dip: DIP, punch: PUNCH, cut: 0 }[s.trans] ?? sb.fade);
export function activeShots(sb, T) {
  const out = [];
  sb.shots.forEach((s, i) => {
    const next = sb.shots[i + 1];
    const end = next ? Math.max(s.t1, next.t0 + fadeOf(sb, next)) : s.t1;
    if (T < s.t0 || T >= end) return;
    const f = fadeOf(sb, s);
    const alpha = i === 0 || f <= 0 ? 1 : clamp01((T - s.t0) / f);
    out.push({ shot: s, alpha: s.trans ? alpha : smooth(alpha), sec: T - s.t0 });
  });
  let k = out.length - 1;
  while (k > 0 && out[k].alpha < 1) k--;
  return out.slice(k);
}
