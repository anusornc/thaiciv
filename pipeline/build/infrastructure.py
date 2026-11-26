"""Build infrastructure.json: Thailand highways, SRT railways, airports (OurAirports) & seaports."""

from __future__ import annotations

import math

from ..core.geo import MapProjection
from ..core.hexgrid import HexGrid
from ..core.store import load_interim, save_web
from ..core.thailand import BY_CODE

REQUIRES = ["_world", "natural_earth", "ourairports", "wikidata_thailand"]
PRODUCES = ["infrastructure.json"]

# Thailand's major commercial seaports & Mekong river port (Port Authority of Thailand / Marine Dept)
# Combined with Wikidata coordinates; annual tonnage where officially published (million metric tons / TEU equiv).
PRINCIPAL_PORTS = [
    ("LCB", "Laem Chabang Port", "coastal", 1, 88000000, 100.8830, 13.0815, "CBI"),
    ("MTP", "Map Ta Phut Industrial Port", "coastal", 2, 42000000, 101.1472, 12.6567, "RYG"),
    ("BKP", "Bangkok Port (Khlong Toei)", "inland", 3, 21000000, 100.5698, 13.7045, "BKK"),
    ("SRC", "Si Racha Harbour", "coastal", 4, 14500000, 100.9182, 13.1683, "CBI"),
    ("STH", "Sattahip Commercial Port", "coastal", 5, 4200000, 100.9167, 12.6250, "CBI"),
    ("SKA", "Songkhla Deep Sea Port", "coastal", 6, 3600000, 100.5844, 7.2247, "SKA"),
    ("PKT", "Phuket Deep Sea Port", "coastal", 7, 1200000, 98.4061, 7.8322, "PKT"),
    ("RNG", "Ranong Andaman Port", "coastal", 8, 950000, 98.6010, 9.9540, "RNG"),
    ("CSN", "Chiang Saen Commercial Port (Mekong)", "inland", 9, 680000, 100.0950, 20.2680, "CRI"),
]


def _rasterize_links(
    lines: list[dict],
    proj: MapProjection,
    grid: HexGrid,
    owner: list[int],
    cls_key: str,
    step_km: float = 2.5,
) -> dict[tuple[int, int], tuple[int, str | None]]:
    links: dict[tuple[int, int], tuple[int, str | None]] = {}
    for ln in lines:
        pts = [proj(lo, la) for lo, la in ln["pts"]]
        cls = int(ln.get(cls_key, 1))
        rname = ln.get("name")
        seq: list[int] = []
        for i in range(len(pts) - 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            dist = math.hypot(x1 - x0, y1 - y0)
            steps = max(1, int(math.ceil(dist / step_km)))
            for s in range(steps + 1):
                t = s / steps
                c = grid.cell_at(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
                if c >= 0 and (not seq or seq[-1] != c):
                    seq.append(c)
        # Drop single-cell corner clips (a-b-c where a and c are already neighbours)
        cleaned: list[int] = []
        for c in seq:
            if len(cleaned) >= 2 and c in grid.neighbours(cleaned[-2]):
                cleaned.pop()
            if not cleaned or cleaned[-1] != c:
                cleaned.append(c)
        for i in range(len(cleaned) - 1):
            a, b = cleaned[i], cleaned[i + 1]
            if a == b or b not in grid.neighbours(a):
                continue
            oa, ob = owner[a], owner[b]
            if oa < 0 and ob < 0:
                continue
            if oa == -2 or ob == -2:
                continue
            pair = (a, b) if a < b else (b, a)
            prev = links.get(pair)
            if prev is None or cls < prev[0]:
                links[pair] = (cls, rname)
    return links


def build() -> None:
    w = load_interim("_world")
    ne = load_interim("natural_earth")
    oa = load_interim("ourairports")

    grid = HexGrid(**w["grid"])
    proj = MapProjection(**w["projection"])
    owner = w["owner"]
    county_arr = w["county"]
    states_fips = w["states"]
    counties_geoid = w["counties"]

    def nearest_thai_cell(x: float, y: float) -> int:
        c = grid.cell_at(x, y)
        if c >= 0 and owner[c] >= 0:
            return c
        if c >= 0:
            for nb in grid.neighbours(c):
                if owner[nb] >= 0:
                    return nb
            for nb in grid.neighbours(c):
                for nb2 in grid.neighbours(nb):
                    if owner[nb2] >= 0:
                        return nb2
        return -1

    road_links = _rasterize_links(ne["roads"], proj, grid, owner, "cls")
    rail_links = _rasterize_links(ne["rail"], proj, grid, owner, "tier")

    roads = [[a, b, cls, name] for (a, b), (cls, name) in sorted(road_links.items())]
    rail = [[a, b, tier] for (a, b), (tier, _) in sorted(rail_links.items())]

    ports = []
    for pid, name, ptype, rank, tons, lon, lat, abbr in PRINCIPAL_PORTS:
        x, y = proj(lon, lat)
        cell = nearest_thai_cell(x, y)
        if cell < 0:
            continue
        pcode = states_fips[owner[cell]]
        ci = county_arr[cell]
        ports.append({
            "id": pid,
            "name": name,
            "type": ptype,
            "rank": rank,
            "tons": tons,
            "domestic": None,
            "foreign": None,
            "imports": None,
            "exports": None,
            "year": 2024,
            "x": round(x, 1),
            "y": round(y, 1),
            "cell": cell,
            "county": counties_geoid[ci] if ci >= 0 else None,
            "cbsa": pcode,
            "state": abbr,
        })

    airports = []
    for ap in oa["airports"]:
        x, y = proj(ap["lon"], ap["lat"])
        cell = nearest_thai_cell(x, y)
        if cell < 0:
            continue
        pcode = states_fips[owner[cell]]
        abbr = BY_CODE[pcode][1]
        ci = county_arr[cell]
        airports.append({
            "id": ap["id"],
            "name": ap["name"],
            "city": ap["city"],
            "hub": ap["hub"],
            "enplanements": ap["enplanements"],
            "enplanements_prev": None,
            "cargo_lbs": None,
            "year": 2024,
            "x": round(x, 1),
            "y": round(y, 1),
            "cell": cell,
            "county": counties_geoid[ci] if ci >= 0 else None,
            "cbsa": pcode,
            "state": abbr,
        })

    save_web(
        "infrastructure.json",
        {
            "version": 1,
            "vintage": {
                "roads": ne.get("vintage", "Natural Earth v5.1.2"),
                "rail": ne.get("vintage", "Natural Earth v5.1.2"),
                "ports": "Port Authority of Thailand / Marine Dept (2024)",
                "airports": oa.get("vintage", "OurAirports 2026 & AOT FY2024"),
            },
            "sources": ["natural_earth", "ourairports", "wikidata_thailand"],
            "rules": {
                "roads": "Natural Earth 1:10m highways & expressways rasterised onto neighbouring Thailand hex links.",
                "rail": "Natural Earth 1:10m State Railway of Thailand (SRT) rail corridors rasterised onto hex links.",
                "ports": "Principal commercial seaports and Chiang Saen Mekong river port (Port Authority of Thailand).",
                "airports": "Scheduled large and medium commercial airports in Thailand from OurAirports with IATA codes.",
            },
            "road_classes": [{"id": "interstate", "name": "Motorway & Trunk Highway"}, {"id": "major", "name": "Major Highway"}],
            "rail_tiers": [{"id": "main", "name": "SRT Main Line"}, {"id": "secondary", "name": "Branch Line"}],
            "hubs": {"L": "Large international hub", "M": "Medium hub", "S": "Regional hub", "N": "Domestic airport"},
            "roads": roads,
            "rail": rail,
            "ports": ports,
            "airports": airports,
        },
    )
