"""Build arsenic.json: geolocated Arsenic (As) monitoring stations, river trends, baseline & national watchpoints."""

from __future__ import annotations

from ..core.geo import MapProjection
from ..core.hexgrid import HexGrid
from ..core.store import load_interim, save_web
from ..core.thailand import BY_CODE

REQUIRES = ["_world", "arsenic_thailand"]
PRODUCES = ["arsenic.json"]

# River display metadata (Thai CSV name → id, English name, transboundary flag, color)
RIVER_META = {
    "แม่น้ำสาย": {"id": "sai", "name": "Sai River (แม่น้ำสาย)", "short": "Sai River", "transboundary": True, "color": "#e0483e"},
    "แม่น้ำกก": {"id": "kok", "name": "Kok River (แม่น้ำกก)", "short": "Kok River", "transboundary": True, "color": "#e68a2e"},
    "แม่น้ำโขง": {"id": "mekong", "name": "Mekong River (แม่น้ำโขง)", "short": "Mekong River", "transboundary": True, "color": "#d4a83b"},
    "แม่น้ำรวก": {"id": "ruak", "name": "Ruak River (แม่น้ำรวก)", "short": "Ruak River", "transboundary": True, "color": "#c95ca8"},
    "แม่น้ำลาว": {"id": "lao", "name": "Lao River (แม่น้ำลาว · Thai control)", "short": "Lao (Control)", "transboundary": False, "color": "#3da872"},
    "แม่น้ำสรวย": {"id": "suai", "name": "Suai River (แม่น้ำสรวย · Thai control)", "short": "Suai (Control)", "transboundary": False, "color": "#3da872"},
    "แม่น้ำกรณ์": {"id": "korn", "name": "Korn River (แม่น้ำกรณ์ · Thai control)", "short": "Korn (Control)", "transboundary": False, "color": "#3da872"},
}

# Verified geographic coordinates (lon, lat) for the 23 official Chiang Rai monitoring stations in the CSV
# Placed along the true river courses (Mae Sai, Chiang Saen / Golden Triangle, Doi Hang, Mueang Chiang Rai, Wiang Chai, Mae Chan, Doi Luang)
STATION_COORDS: dict[str, tuple[float, float, str]] = {
    # Kok River (upstream west → downstream northeast to Mekong confluence at Sop Kok)
    "KK04":  (99.645, 19.952, "Ban Chadoe, Doi Hang"),
    "KK05":  (99.720, 19.942, "Mae Yao–Doi Hang Bridge"),
    "KK06":  (99.760, 19.930, "Ban Pong Na Kham, Doi Hang"),
    "KK07":  (99.795, 19.922, "Kok River Bridge, Doi Hang"),
    "KK08":  (99.832, 19.918, "Mae Fah Luang Bridge, Mueang CR"),
    "KK09":  (99.855, 19.921, "Chaloem Phrakiat 1 Bridge"),
    "KK010": (99.878, 19.925, "Chiang Rai Weir (ฝายเชียงราย)"),
    "KK011": (99.935, 19.955, "Rim Kok–Wiang Nuea Bridge, Wiang Chai"),
    "KK012": (99.980, 20.015, "Yonok Nakhon Bridge, Mae Khao Tom"),
    "KK013": (100.035, 20.105, "Tha Khao Plueak, Mae Chan"),
    "KK014": (100.095, 20.170, "Nong Pa Ko, Doi Luang"),
    "KK015": (100.145, 20.235, "Ban Saeo, Chiang Saen (Kok Mouth)"),
    # Sai River (Mae Sai border)
    "SA01":  (99.875, 20.445, "Ban Hua Fai, Mae Sai"),
    "SA02":  (99.912, 20.438, "2nd Thai–Myanmar Friendship Bridge"),
    "SA03":  (99.965, 20.415, "Ban Pa Sang Ngam, Ko Chang"),
    # Ruak River (Ko Chang PWA intake → Golden Triangle confluence)
    "RU01":  (100.015, 20.380, "Ko Chang PWA Water Intake, Mae Sai"),
    "RU02":  (100.075, 20.355, "Ruak River Mouth, Chiang Saen"),
    # Mekong River (Golden Triangle → Chiang Saen → Sop Kok)
    "NK01":  (100.083, 20.352, "Golden Triangle Border Point"),
    "NK02":  (100.095, 20.275, "Wiang, Chiang Saen"),
    "NK03":  (100.155, 20.242, "Ban Sop Kok, Chiang Saen"),
    # Thai-origin control tributaries (safe baseline <0.010 mg/L)
    "KO01":  (99.845, 19.855, "Korn River, Tha Sai (Control)"),
    "LA01":  (99.960, 19.860, "Lao River, Wiang Chai (Control)"),
    "SU01":  (99.545, 19.655, "Suai River, Mae Suai (Control)"),
}

# National arsenic watchpoints / documented hotspots outside the Chiang Rai CSV (transparently flagged as watchpoints)
WATCHPOINTS = [
    {
        "id": "wp-kk01-maeai",
        "name": "Kok River Entry · Tha Ton (KK01–KK03)",
        "th_name": "แม่น้ำกก ชายแดน ต.ท่าตอน อ.แม่อาย",
        "river": "Kok River (Upstream Entry)",
        "category": "transboundary_active",
        "lon": 99.358,
        "lat": 20.068,
        "province": "CMI",
        "status": "Active transboundary crisis (2025–2026)",
        "summary": "Upstream entry of the Kok River from Shan State, Myanmar; repeated PCD surface-water & sediment As exceedances; proposed head of Thailand's ~150 km Kok Pollution Control Zone.",
        "source": "PCD / REO1 (2025–2026)",
    },
    {
        "id": "wp-salween",
        "name": "Salween River Basin (Mae Sariang–Sop Moei)",
        "th_name": "ลุ่มน้ำสาละวิน จ.แม่ฮ่องสอน",
        "river": "Salween River",
        "category": "transboundary_active",
        "lon": 97.725,
        "lat": 18.145,
        "province": "MSN",
        "status": "Active transboundary watchpoint (2025–2026)",
        "summary": "Monitored by PCD / REO1 for transboundary arsenic & heavy-metal runoff from upstream mining in Shan & Kayah States, Myanmar.",
        "source": "PCD / REO1 (2025–2026)",
    },
    {
        "id": "wp-ronphibun",
        "name": "Ron Phibun Historic Arsenic Zone",
        "th_name": "อ.ร่อนพิบูลย์ จ.นครศรีธรรมราช",
        "river": "Groundwater & Old Tin Tailings",
        "category": "historic_mining",
        "lon": 99.855,
        "lat": 8.178,
        "province": "NRT",
        "status": "Historic & long-term surveillance site",
        "summary": "Thailand's landmark chronic arsenic poisoning site ('Black Fever' / โรคไข้ดำ since 1987) linked to arsenopyrite leaching from legacy tin & tungsten mines into shallow groundwater.",
        "source": "MOPH / DMR",
    },
    {
        "id": "wp-chatree",
        "name": "Chatree Gold Mine Belt (Phichit–Phetchabun)",
        "th_name": "พื้นที่รอบเหมืองแร่ทองคำชาตรี (พิจิตร–เพชรบูรณ์)",
        "river": "Local Watersheds & Groundwater",
        "category": "surveillance",
        "lon": 100.625,
        "lat": 16.280,
        "province": "PCT",
        "status": "Ongoing environmental surveillance",
        "summary": "Subject of Department of Mineral Resources (DMR 2565) heavy-metal environmental contamination studies and ongoing local health & water monitoring.",
        "source": "DMR (data.dmr.go.th, 2022)",
    },
    {
        "id": "wp-banrai",
        "name": "Ban Rai Geological Arsenic Study Area",
        "th_name": "อ.บ้านไร่ จ.อุทัยธานี",
        "river": "Geological / Soil & Water",
        "category": "surveillance",
        "lon": 99.520,
        "lat": 15.085,
        "province": "UTI",
        "status": "DMR geological survey zone",
        "summary": "Investigated by Department of Mineral Resources (DMR 2564) for natural and mining-related arsenic distribution in the environment.",
        "source": "DMR (data.dmr.go.th, 2021)",
    },
]


def build() -> None:
    w = load_interim("_world")
    raw = load_interim("arsenic_thailand")

    grid = HexGrid(**w["grid"])
    proj = MapProjection(**w["projection"])
    owner = w["owner"]
    county_arr = w["county"]
    states_fips = w["states"]
    counties_geoid = w["counties"]
    std_as = raw["standard_as_mg_l"]

    def locate(lon: float, lat: float):
        x, y = proj(lon, lat)
        c = grid.cell_at(x, y)
        if c < 0 or owner[c] < 0:
            if c >= 0:
                for nb in grid.neighbours(c):
                    if owner[nb] >= 0:
                        c = nb
                        break
        if c < 0 or owner[c] < 0:
            land = [i for i, o in enumerate(owner) if o >= 0]
            c = min(land, key=lambda i: (grid.cx(i) - x) ** 2 + (grid.cy(i) - y) ** 2)
        pcode = states_fips[owner[c]]
        ci = county_arr[c]
        return round(x, 1), round(y, 1), c, counties_geoid[ci] if ci >= 0 else None, pcode, BY_CODE[pcode][1]

    stations_out = []
    by_river_acc: dict[str, dict] = {}
    round_series: dict[str, dict[int, list[float]]] = {}

    for st in raw["stations"]:
        sid = st["id"]
        lon, lat, en_name = STATION_COORDS.get(sid, (99.83, 19.91, sid))
        x, y, cell, county, pcode, abbr = locate(lon, lat)
        rm = RIVER_META.get(
            st["river_th"],
            {"id": "other", "name": st["river_th"], "short": st["river_th"], "transboundary": True, "color": "#d4a83b"},
        )

        # Compute As, Pb, Mn stats across sampled rounds
        as_vals = []
        as_exceed = 0
        pb_max = None
        mn_max = None
        rounds_clean = []
        for r in st["rounds"]:
            a = r["as"]
            p = r["pb"]
            m = r["mn"]
            if a is not None:
                is_ex = (not a["below_dl"]) and (a["val"] > std_as)
                if is_ex:
                    as_exceed += 1
                as_vals.append(a["val"])
                round_series.setdefault(rm["id"], {}).setdefault(r["round"], []).append(a["val"])
            if p is not None and not p["below_dl"]:
                pb_max = max(pb_max or 0.0, p["val"])
            if m is not None and not m["below_dl"]:
                mn_max = max(mn_max or 0.0, m["val"])
            rounds_clean.append({
                "round": r["round"],
                "as": a["val"] if a else None,
                "as_raw": a["raw"] if a else None,
                "as_below_dl": a["below_dl"] if a else None,
                "pb_raw": p["raw"] if p else None,
                "mn_raw": m["raw"] if m else None,
            })

        sampled = len(as_vals)
        max_as = round(max(as_vals), 4) if as_vals else None
        mean_as = round(sum(as_vals) / sampled, 4) if sampled else None
        latest_sampled = next((r for r in reversed(rounds_clean) if r["as"] is not None), None)
        latest_as = latest_sampled["as"] if latest_sampled else None
        latest_raw = latest_sampled["as_raw"] if latest_sampled else None

        if max_as is not None and max_as > 0.03:
            severity = "severe"
        elif as_exceed > 0:
            severity = "exceed"
        else:
            severity = "safe"

        stations_out.append({
            "id": sid,
            "name": en_name,
            "location_th": st["location_th"],
            "river_id": rm["id"],
            "river": rm["name"],
            "river_short": rm["short"],
            "transboundary": rm["transboundary"],
            "color": rm["color"],
            "severity": severity,
            "max_as": max_as,
            "mean_as": mean_as,
            "latest_as": latest_as,
            "latest_raw": latest_raw,
            "exceed_rounds": as_exceed,
            "sampled_rounds": sampled,
            "ratio_max": round(max_as / std_as, 1) if max_as is not None else None,
            "max_pb": round(pb_max, 4) if pb_max is not None else None,
            "max_mn": round(mn_max, 4) if mn_max is not None else None,
            "rounds": rounds_clean,
            "x": x,
            "y": y,
            "cell": cell,
            "county": county,
            "cbsa": pcode,
            "state": abbr,
            "lon": lon,
            "lat": lat,
        })

        acc = by_river_acc.setdefault(
            rm["id"],
            {
                "id": rm["id"],
                "name": rm["name"],
                "short": rm["short"],
                "transboundary": rm["transboundary"],
                "color": rm["color"],
                "stations": 0,
                "exceeding_stations": 0,
                "max_as": 0.0,
                "vals": [],
                "exceed_samples": 0,
                "total_samples": 0,
            },
        )
        acc["stations"] += 1
        if as_exceed > 0:
            acc["exceeding_stations"] += 1
        if max_as is not None and max_as > acc["max_as"]:
            acc["max_as"] = max_as
        acc["vals"].extend(as_vals)
        acc["exceed_samples"] += as_exceed
        acc["total_samples"] += sampled

    stations_out.sort(key=lambda s: (-(s["max_as"] or 0.0), s["id"]))

    rivers_out = []
    for rid, acc in by_river_acc.items():
        r_trend = []
        for rn in range(1, 9):
            vs = round_series.get(rid, {}).get(rn, [])
            r_trend.append({
                "round": rn,
                "mean_as": round(sum(vs) / len(vs), 4) if vs else None,
                "max_as": round(max(vs), 4) if vs else None,
                "n": len(vs),
            })
        rivers_out.append({
            "id": acc["id"],
            "name": acc["name"],
            "short": acc["short"],
            "transboundary": acc["transboundary"],
            "color": acc["color"],
            "stations": acc["stations"],
            "exceeding_stations": acc["exceeding_stations"],
            "max_as": round(acc["max_as"], 4),
            "mean_as": round(sum(acc["vals"]) / len(acc["vals"]), 4) if acc["vals"] else None,
            "exceed_samples": acc["exceed_samples"],
            "total_samples": acc["total_samples"],
            "by_round": r_trend,
        })
    rivers_out.sort(key=lambda r: (-int(r["transboundary"]), -(r["max_as"] or 0.0)))

    watchpoints_out = []
    for wp in WATCHPOINTS:
        x, y, cell, county, pcode, abbr = locate(wp["lon"], wp["lat"])
        watchpoints_out.append({
            **wp,
            "x": x,
            "y": y,
            "cell": cell,
            "county": county,
            "cbsa": pcode,
            "state": abbr,
        })

    trans_sts = [s for s in stations_out if s["transboundary"]]
    ctrl_sts = [s for s in stations_out if not s["transboundary"]]

    save_web(
        "arsenic.json",
        {
            "version": 1,
            "vintage": raw.get("vintage"),
            "sources": ["arsenic_thailand"],
            "standards": {
                "as_mg_l": std_as,
                "pb_mg_l": raw["standard_pb_mg_l"],
                "mn_mg_l": raw["standard_mn_mg_l"],
                "note": "Thailand Surface Water Quality Standard (PCD) & WHO drinking-water guideline: Arsenic (As) ≤ 0.010 mg/L.",
            },
            "caveats": (
                "Official open-data station CSVs currently cover 23 stations across Chiang Rai's Kok, Sai, Ruak, Mekong and "
                "control tributaries (8 rounds). Values reported as '<0.010' are below detection limit (plotted at 0.005 mg/L in "
                "trends and counted as compliant); '0' indicates a station was not sampled in that round. Separate PCD press "
                "briefings in late 2026 reported flood-season spikes up to 0.284 mg/L in the Sai River. National watchpoints "
                "(Mae Ai KK01–03, Salween, Ron Phibun, Chatree, Ban Rai) are context markers without a unified national CSV."
            ),
            "summary": {
                "total_stations": len(stations_out),
                "exceeding_stations": sum(1 for s in stations_out if s["exceed_rounds"] > 0),
                "transboundary_stations": len(trans_sts),
                "transboundary_exceeding": sum(1 for s in trans_sts if s["exceed_rounds"] > 0),
                "control_stations": len(ctrl_sts),
                "control_exceeding": sum(1 for s in ctrl_sts if s["exceed_rounds"] > 0),
                "peak_as_mg_l": max((s["max_as"] or 0.0) for s in stations_out),
                "peak_station": stations_out[0]["id"] if stations_out else None,
                "pcd_flood_peak_note": "Up to 0.284 mg/L (~28× standard) reported by PCD in Sai River flood peaks (2026).",
                "watchpoints_count": len(watchpoints_out),
            },
            "rivers": rivers_out,
            "stations": stations_out,
            "baseline": raw["baseline"],
            "watchpoints": watchpoints_out,
        },
    )
