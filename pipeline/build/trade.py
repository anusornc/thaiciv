"""Build trade.json: Thailand's major domestic economic & freight corridors between the 7 NESDC regions."""

from __future__ import annotations

import heapq
import json
import math

from ..core.hexgrid import HexGrid
from ..core.paths import WEB_DATA
from ..core.store import load_interim, save_web

REQUIRES = ["_world", "nesdc_gpp", "cities.json", "infrastructure.json"]
PRODUCES = ["trade.json"]

# Major domestic corridors connecting Thailand's economic hubs (gravity-scaled by NESDC 2024p GPP)
# Clearly noted as schematic economic corridors routed along Thailand's real highway/SRT rail links.
CORRIDOR_PAIRS = [
    ("10", "20", "truck", "auto", "Bangkok – Eastern Economic Corridor (Chon Buri / Laem Chabang)"),
    ("10", "21", "pipeline", "petro", "Bangkok – Rayong (Map Ta Phut Petrochemical & Energy)"),
    ("10", "14", "truck", "elec", "Bangkok – Ayutthaya (Northern Industrial Estate Corridor)"),
    ("10", "30", "truck", "mixed", "Bangkok – Nakhon Ratchasima (Mittraphap Gateway to Isan)"),
    ("10", "50", "air", "tour", "Bangkok – Chiang Mai (Northern Trunk & Air Corridor)"),
    ("10", "83", "air", "tour", "Bangkok – Phuket (Andaman Tourism Corridor)"),
    ("10", "90", "rail", "agri", "Bangkok – Songkhla / Hat Yai (Southern Trunk to Malaysia)"),
    ("10", "70", "truck", "agri", "Bangkok – Ratchaburi (Western Corridor)"),
    ("10", "40", "truck", "mixed", "Bangkok – Khon Kaen (Central Isan Hub)"),
    ("10", "84", "truck", "agri", "Bangkok – Surat Thani (Upper South & Gulf Islands)"),
    ("30", "40", "truck", "agri", "Nakhon Ratchasima – Khon Kaen (Mittraphap Isan Spine)"),
    ("40", "41", "truck", "mixed", "Khon Kaen – Udon Thani (Lao PDR / Nong Khai Trade Link)"),
    ("30", "34", "rail", "agri", "Nakhon Ratchasima – Ubon Ratchathani (Lower Isan Rail)"),
    ("20", "30", "truck", "auto", "Chon Buri / Laem Chabang – Korat (EEC–Isan Freight Link)"),
    ("50", "57", "truck", "agri", "Chiang Mai – Chiang Rai (Upper North / Mekong Link)"),
    ("50", "65", "truck", "agri", "Chiang Mai – Phitsanulok (Indo-China Crossroads)"),
    ("65", "40", "truck", "mixed", "Phitsanulok – Khon Kaen (East-West Economic Corridor)"),
    ("84", "83", "truck", "tour", "Surat Thani – Phuket (Trans-Peninsula Gulf–Andaman)"),
    ("84", "90", "rail", "agri", "Surat Thani – Songkhla / Hat Yai (Southern Peninsula)"),
    ("20", "22", "truck", "agri", "Chon Buri – Chanthaburi (Eastern Fruit & Border Corridor)"),
]

COMMODITIES = {
    "auto": "Automotive, electronics & industrial parts",
    "petro": "Petrochemicals, refined fuels & natural gas",
    "elec": "Electronics & machinery",
    "mixed": "Mixed consumer & wholesale freight",
    "tour": "Tourism, aviation & hospitality services",
    "agri": "Rice, rubber, sugar, fruit & agricultural produce",
}


def _shortest_path(grid: HexGrid, owner: list[int], road_cost: dict[tuple[int, int], float], start: int, goal: int) -> list[int]:
    pq = [(0.0, start)]
    dist = {start: 0.0}
    prev: dict[int, int] = {}
    gx, gy = grid.cx(goal), grid.cy(goal)
    while pq:
        d, u = heapq.heappop(pq)
        if u == goal:
            break
        if d > dist.get(u, 1e18):
            continue
        for v in grid.neighbours(u):
            if owner[v] == -2:
                continue
            pair = (u, v) if u < v else (v, u)
            step = road_cost.get(pair, 6.0 if owner[v] >= 0 else 18.0)
            nd = d + step
            if nd < dist.get(v, 1e18):
                dist[v] = nd
                prev[v] = u
                h = math.hypot(grid.cx(v) - gx, grid.cy(v) - gy) / (grid.radius * 2.0) * 0.8
                heapq.heappush(pq, (nd + h, v))
    if goal not in prev and goal != start:
        return [start, goal]
    path = [goal]
    cur = goal
    while cur != start:
        cur = prev[cur]
        path.append(cur)
    path.reverse()
    return path


def build() -> None:
    w = load_interim("_world")
    gpp = load_interim("nesdc_gpp")
    cities = json.loads((WEB_DATA / "cities.json").read_text(encoding="utf-8"))
    infra = json.loads((WEB_DATA / "infrastructure.json").read_text(encoding="utf-8"))

    grid = HexGrid(**w["grid"])
    owner = w["owner"]
    city_by_id = {c["id"]: c for c in cities}

    road_cost: dict[tuple[int, int], float] = {}
    for a, b, cls, _ in infra.get("roads", []):
        pair = (a, b) if a < b else (b, a)
        road_cost[pair] = 1.0 if cls == 0 else 1.8
    for a, b, tier in infra.get("rail", []):
        pair = (a, b) if a < b else (b, a)
        road_cost[pair] = min(road_cost.get(pair, 9.0), 1.4 if tier == 0 else 2.2)

    # Zones = major economic hub provinces present in CORRIDOR_PAIRS
    zone_ids = sorted({x for a, b, *_ in CORRIDOR_PAIRS for x in (a, b) if x in city_by_id})
    zones = []
    partners_map: dict[str, list] = {zid: [] for zid in zone_ids}

    routes = []
    for a, b, top_mode, comm, _desc in CORRIDOR_PAIRS:
        if a not in city_by_id or b not in city_by_id:
            continue
        ca, cb = city_by_id[a], city_by_id[b]
        dist_km = max(40.0, math.hypot(ca["x"] - cb["x"], ca["y"] - cb["y"]))
        # Economic corridor intensity index from NESDC GPP (Millions THB proxy; clearly noted in path_note!)
        ga = (ca.get("gdp") or 0) / 1e9  # Billion THB
        gb = (cb.get("gdp") or 0) / 1e9
        val_m = round(math.sqrt(ga * gb) * 180.0 / math.pow(dist_km / 150.0, 0.45), 1)
        path = _shortest_path(grid, owner, road_cost, ca["cell"], cb["cell"])
        modes = {m: 0.0 for m in ("truck", "rail", "water", "air", "multiple", "pipeline", "other")}
        modes[top_mode] = 0.72
        modes["truck" if top_mode != "truck" else "rail"] = 0.20
        modes["other"] = 0.08
        routes.append({
            "a": a,
            "b": b,
            "rank": 0,
            "value_musd": val_m,
            "tons_k": round(val_m * 1.4, 1),
            "tmiles_m": round(val_m * dist_km * 0.001, 1),
            "modes": modes,
            "top_mode": top_mode,
            "top_commodity": comm,
            "dist_km": round(dist_km),
            "path": path,
        })
        partners_map[a].append([b, val_m, top_mode])
        partners_map[b].append([a, val_m, top_mode])

    routes.sort(key=lambda r: -r["value_musd"])
    for i, r in enumerate(routes, 1):
        r["rank"] = i

    for zid in zone_ids:
        c = city_by_id[zid]
        ps = sorted(partners_map[zid], key=lambda x: -x[1])[:5]
        tot_out = round(sum(x[1] for x in ps), 1)
        zones.append({
            "id": zid,
            "faf": [zid],
            "name": c["full"],
            "short": c["name"],
            "kind": "metro",
            "states": c["states"],
            "cities": [zid],
            "counties": len(c["counties"]),
            "anchor": {"cell": c["cell"], "x": c["x"], "y": c["y"], "city": zid},
            "partners": ps,
            "totals_musd": {"within": round((c.get("gdp") or 0) / 1e6 * 0.25, 1), "other_zones": tot_out, "import": None, "export": None},
        })

    nat_gdp_m = round(((gpp.get("national") or {}).get("gpp_thb") or 0) / 1e6, 1)
    save_web(
        "trade.json",
        {
            "version": 1,
            "vintage": f"NESDC GPP {gpp['year']}p & Thailand Highway/SRT Corridors",
            "year": gpp["year"],
            "sources": ["nesdc_gpp", "natural_earth"],
            "rule": "20 major domestic economic corridors connecting Thailand's principal provincial hubs, weighted by NESDC 2024p GPP and distance.",
            "path_note": "Thailand does not publish an inter-provincial O-D freight survey like the US FAF5; these arcs show major national highway, rail, air and pipeline corridors routed along Natural Earth road & SRT rail hex links, scaled by NESDC GPP gravity.",
            "units": {"value_musd": "corridor gravity index (M฿ scale)", "tons_k": "estimated corridor index", "tmiles_m": "index"},
            "modes": [
                {"id": "truck", "name": "Highway / Truck"},
                {"id": "rail", "name": "SRT Rail"},
                {"id": "water", "name": "Coastal / River"},
                {"id": "air", "name": "Air"},
                {"id": "multiple", "name": "Intermodal"},
                {"id": "pipeline", "name": "Gas / Petro Pipeline"},
                {"id": "other", "name": "Other"},
            ],
            "commodities": COMMODITIES,
            "national_musd": {"domestic": nat_gdp_m, "import": None, "export": None},
            "zones": zones,
            "routes": routes,
        },
    )
