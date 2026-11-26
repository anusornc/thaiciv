// Arsenic & heavy-metal river monitoring map layer + Map menu toggle.
// Draws the 23 official Chiang Rai / PCD stations (color-coded against Thailand's 0.010 mg/L standard)
// and 5 national watchpoints (Mae Ai KK01–03, Salween, Ron Phibun, Chatree, Ban Rai).
import { esc } from "../../format.js";
import { t, isTh, getLang, onLangChange, arsenicWatchpoint } from "../../i18n.js";

const COLORS = {
  severe: "#e03838", // > 0.030 mg/L (> 3× Thai standard)
  exceed: "#e88a2e", // > 0.010 – 0.030 mg/L (1–3× standard)
  safe: "#38a872",   // ≤ 0.010 mg/L (within standard / Thai control)
  watch: "#a06ee0",  // National context watchpoint (no CSV series)
};

function fmtAs(v) {
  return v == null ? "–" : `${Number(v).toFixed(3)} mg/L`;
}

export function install(app) {
  let data = null;
  let on = true;
  let ver = 0;

  const sites = () => {
    if (!data) return [];
    const out = [];
    for (const s of data.stations || []) {
      out.push({ kind: "station", data: s, x: s.x, y: s.y, cell: s.cell, color: COLORS[s.severity] || COLORS.exceed });
    }
    for (const wp of data.watchpoints || []) {
      out.push({ kind: "watchpoint", data: wp, x: wp.x, y: wp.y, cell: wp.cell, color: COLORS.watch });
    }
    return out;
  };

  app.registerStaticLayer({
    id: "arsenic",
    z: 67,
    minRpx: 1.5,
    visible: () => on && !!data,
    sig: () => `v${ver}:${getLang()}`,
    draw(ctx, vp, w, o) {
      const list = sites();
      if (!list.length) return;
      const { Rpx } = o;
      const rSt = Math.max(4.5, Math.min(10, Rpx * 0.42));
      const rWp = Math.max(5.5, Math.min(10.5, Rpx * 0.46));
      o.screen();

      // Draw stations first, watchpoints on top (severe last so worst hotspots stay visible)
      const order = { safe: 0, exceed: 1, severe: 2, watch: 3 };
      const sorted = [...list].sort((a, b) => (order[a.kind === "watchpoint" ? "watch" : a.data.severity] ?? 0) - (order[b.kind === "watchpoint" ? "watch" : b.data.severity] ?? 0));

      for (const it of sorted) {
        const [sx, sy] = o.toScreen(it.x, it.y);
        if (sx < -30 || sy < -30 || sx > ctx.canvas.width / vp.dpr + 30 || sy > ctx.canvas.height / vp.dpr + 30) continue;

        ctx.save();
        if (it.kind === "watchpoint") {
          // Diamond badge with gold rim for national watchpoints
          ctx.beginPath();
          ctx.moveTo(sx, sy - rWp);
          ctx.lineTo(sx + rWp, sy);
          ctx.lineTo(sx, sy + rWp);
          ctx.lineTo(sx - rWp, sy);
          ctx.closePath();
          ctx.fillStyle = it.color;
          ctx.fill();
          ctx.lineWidth = 1.6;
          ctx.strokeStyle = "#f2d68a";
          ctx.stroke();
        } else {
          // Outer dark halo + crisp color-coded circle
          if (it.data.severity === "severe") {
            ctx.beginPath();
            ctx.arc(sx, sy, rSt + 3.2, 0, Math.PI * 2);
            ctx.fillStyle = "rgba(224, 56, 56, 0.28)";
            ctx.fill();
          }
          ctx.beginPath();
          ctx.arc(sx, sy, rSt, 0, Math.PI * 2);
          ctx.fillStyle = it.color;
          ctx.fill();
          ctx.lineWidth = 1.5;
          ctx.strokeStyle = "#16110a";
          ctx.stroke();

          // Tiny inner dot for severe stations
          if (it.data.severity === "severe" && rSt >= 5.5) {
            ctx.beginPath();
            ctx.arc(sx, sy, rSt * 0.34, 0, Math.PI * 2);
            ctx.fillStyle = "#fff4d8";
            ctx.fill();
          }
        }

        // Station labels when zoomed into the river basin
        if (Rpx >= 13) {
          const wp = it.kind === "watchpoint" ? arsenicWatchpoint(it.data) : null;
          const lbl = wp
            ? wp.name.split(" (")[0]
            : `${it.data.id} · ${it.data.max_as != null ? it.data.max_as.toFixed(3) : "–"}`;
          ctx.font = `600 10px -apple-system, "Thonburi", "Noto Sans Thai", system-ui, sans-serif`;
          ctx.textBaseline = "middle";
          ctx.textAlign = "left";
          ctx.lineWidth = 3;
          ctx.strokeStyle = "rgba(12, 16, 22, 0.88)";
          ctx.strokeText(lbl, sx + rSt + 4, sy);
          ctx.fillStyle = it.kind === "watchpoint" ? "#e5d4ff" : it.data.severity === "safe" ? "#a8f0c8" : "#ffe6c4";
          ctx.fillText(lbl, sx + rSt + 4, sy);
        }
        ctx.restore();
      }
      o.world();
    },
    hit(xKm, yKm, Rpx) {
      if (!data) return null;
      const hitKm = Math.max(8, (12 / Math.max(1, Rpx)) * app.w.grid.R);
      let best = null;
      let bestD = hitKm * hitKm;
      for (const it of sites()) {
        const d2 = (it.x - xKm) ** 2 + (it.y - yKm) ** 2;
        if (d2 < bestD) {
          bestD = d2;
          best = it;
        }
      }
      return best;
    },
    tooltip(it) {
      if (!it) return null;
      const d = it.data;
      if (it.kind === "watchpoint") {
        const wp = arsenicWatchpoint(d);
        return `<b>${esc(wp.name)}</b><br><span class="muted">${esc(isTh() ? d.name : d.th_name)}</span><br>` +
          `<span style="color:#c9a8ff">${esc(wp.status)}</span><br>${esc(wp.summary)}<br>` +
          `<span class="muted">${t("Source", "แหล่งข้อมูล")}: ${esc(wp.source)} · ${t("Click to open Water & Arsenic Advisor", "คลิกเพื่อเปิดแดชบอร์ดน้ำและสารหนู")}</span>`;
      }
      const badge = d.severity === "severe"
        ? `<span style="color:#ff7878"><b>${t(`SEVERE · ${d.ratio_max}× std`, `รุนแรง · ${d.ratio_max}× มาตรฐาน`)}</b></span>`
        : d.severity === "exceed"
          ? `<span style="color:#ffb65c"><b>${t(`EXCEEDS · ${d.ratio_max}× std`, `เกินมาตรฐาน · ${d.ratio_max}×`)}</b></span>`
          : `<span style="color:#78dfa8"><b>${t("WITHIN STD (≤ 0.010 mg/L)", "ปกติ (≤ 0.010 มก./ล.)")}</b></span>`;
      const extra = [
        d.max_pb != null ? `Pb max ${d.max_pb.toFixed(3)}` : null,
        d.max_mn != null ? `Mn max ${d.max_mn.toFixed(2)}` : null,
      ].filter(Boolean).join(" · ");
      const peakStr = d.exceed_rounds === 0 && d.max_as <= 0.005 ? t("<0.010 mg/L", "<0.010 มก./ล.") : fmtAs(d.max_as);
      return `<b>${esc(d.id)} · ${esc(isTh() ? (d.location_th || d.name) : d.name)}</b><br><span class="muted">${esc(d.river)} · ${esc(isTh() ? d.name : d.location_th)}</span><br>` +
        `${t("Peak As", "ค่าสารหนูสูงสุด")}: <b>${esc(peakStr)}</b> (${badge})<br>` +
        `${t("Exceeding rounds", "รอบที่เกินมาตรฐาน")}: <b>${d.exceed_rounds} / ${d.sampled_rounds}</b>` +
        (extra ? ` <span class="muted">· ${esc(extra)} mg/L</span>` : "") +
        `<br><span class="muted">${t("Click to inspect in Water & Arsenic Advisor", "คลิกเพื่อดูรายละเอียดในแดชบอร์ดน้ำและสารหนู")}</span>`;
    },
    click(it) {
      if (!it) return false;
      if (app.hasMode?.("advisor")) {
        app.setMode("advisor", { id: "arsenic", station: it.data.id });
        return true;
      }
      return false;
    },
  });

  app.ui.addMapToggle({
    id: "arsenic",
    label: "Arsenic (As)",
    icon: "l-disasters",
    default: true,
    title: "Surface-water Arsenic (As) monitoring stations (Chiang Rai / PCD) & national watchpoints",
    get: () => on,
    set(v) {
      on = !!v;
      ver++;
      app.redraw?.();
    },
  });

  // Load arsenic.json right away so markers appear cleanly on first view
  app.loadData("arsenic").then((d) => {
    if (!d) return;
    data = d;
    ver++;
    app.redraw?.();
  });
  onLangChange(() => {
    ver++;
    app.invalidate?.();
  });
}
