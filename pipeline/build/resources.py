"""Build resources.json from WRI Global Power Plant Database (Thailand)."""

from __future__ import annotations

from ..core.geo import MapProjection
from ..core.hexgrid import HexGrid
from ..core.store import load_interim, save_web
from ..core.thailand import BY_CODE

REQUIRES = ["_world", "wri_power"]
PRODUCES = ["resources.json"]

RESOURCE_TYPES = [
    {
        "id": "gas_plant",
        "name": "Natural gas plant",
        "category": "energy",
        "emoji": "🔥",
        "icon": "r-gas_plant",
        "color": "#e07b39",
        "unit": "MW",
        "description": "Natural gas power stations ≥ 50 MW (Thailand's primary baseload power, WRI GPPD).",
        "source": "wri_power",
    },
    {
        "id": "coal_plant",
        "name": "Coal / lignite plant",
        "category": "energy",
        "emoji": "🏭",
        "icon": "r-coal_plant",
        "color": "#585858",
        "unit": "MW",
        "description": "Coal and lignite plants ≥ 50 MW including Mae Moh (Lampang), BLCP and Gheco-One (Rayong).",
        "source": "wri_power",
    },
    {
        "id": "hydro",
        "name": "Hydroelectric dam",
        "category": "energy",
        "emoji": "💧",
        "icon": "r-hydro",
        "color": "#3d9be0",
        "unit": "MW",
        "description": "Hydroelectric dams ≥ 10 MW (Bhumibol, Sirikit, Srinagarind, Vajiralongkorn, Lam Takhong, etc.).",
        "source": "wri_power",
    },
    {
        "id": "solar",
        "name": "Solar farm",
        "category": "energy",
        "emoji": "☀️",
        "icon": "r-solar",
        "color": "#e6b82e",
        "unit": "MW",
        "description": "Utility-scale solar photovoltaic farms ≥ 15 MW (Central Plains, Lop Buri, Nakhon Pathom, Isan).",
        "source": "wri_power",
    },
    {
        "id": "wind",
        "name": "Wind farm",
        "category": "energy",
        "emoji": "🌬️",
        "icon": "r-wind",
        "color": "#5ec4c4",
        "unit": "MW",
        "description": "Utility wind farms ≥ 10 MW (Khorat Plateau ridges in Nakhon Ratchasima & Chaiyaphum, Southern coast).",
        "source": "wri_power",
    },
    {
        "id": "biomass",
        "name": "Biomass & biogas",
        "category": "energy",
        "emoji": "🌿",
        "icon": "r-biomass",
        "color": "#64a846",
        "unit": "MW",
        "description": "Sugarcane bagasse, rice-husk and biomass power stations ≥ 15 MW.",
        "source": "wri_power",
    },
    {
        "id": "oil_plant",
        "name": "Oil thermal plant",
        "category": "energy",
        "emoji": "🛢️",
        "icon": "r-oil_plant",
        "color": "#453a32",
        "unit": "MW",
        "description": "Fuel-oil thermal stations ≥ 20 MW.",
        "source": "wri_power",
    },
]

MIN_MW = {
    "gas_plant": 50.0,
    "coal_plant": 50.0,
    "hydro": 10.0,
    "solar": 15.0,
    "wind": 10.0,
    "biomass": 15.0,
    "oil_plant": 20.0,
}


def build() -> None:
    w = load_interim("_world")
    wri = load_interim("wri_power")

    grid = HexGrid(**w["grid"])
    proj = MapProjection(**w["projection"])
    owner = w["owner"]
    states_fips = w["states"]

    def nearest_thai_cell(x: float, y: float) -> int:
        c = grid.cell_at(x, y)
        if c >= 0 and owner[c] >= 0:
            return c
        if c >= 0:
            for nb in grid.neighbours(c):
                if owner[nb] >= 0:
                    return nb
        return -1

    items = []
    for p in wri["plants"]:
        rtype = p["type"]
        if rtype not in MIN_MW or p["capacity_mw"] < MIN_MW[rtype]:
            continue
        x, y = proj(p["lon"], p["lat"])
        cell = nearest_thai_cell(x, y)
        if cell < 0:
            continue
        pcode = states_fips[owner[cell]]
        abbr = BY_CODE[pcode][1]
        parts = [p["fuel"]]
        if p.get("owner"):
            parts.append(p["owner"])
        if p.get("year"):
            parts.append(f"est. {p['year'][:4]}")
        items.append({
            "type": rtype,
            "name": p["name"],
            "x": round(x, 1),
            "y": round(y, 1),
            "cell": cell,
            "value": round(p["capacity_mw"], 1),
            "detail": " · ".join(parts),
            "state": abbr,
            "cbsa": pcode,
        })

    # Summary by type (national and per province)
    nat_sum = {t["id"]: {"count": 0, "value": 0.0, "unit": t["unit"]} for t in RESOURCE_TYPES}
    st_sum: dict[str, dict] = {}
    for it in items:
        t = it["type"]
        v = it["value"] or 0.0
        nat_sum[t]["count"] += 1
        nat_sum[t]["value"] = round(nat_sum[t]["value"] + v, 1)
        st = st_sum.setdefault(it["state"], {})
        if t not in st:
            st[t] = {"count": 0, "value": 0.0, "unit": "MW"}
        st[t]["count"] += 1
        st[t]["value"] = round(st[t]["value"] + v, 1)

    save_web(
        "resources.json",
        {
            "types": RESOURCE_TYPES,
            "items": items,
            "summary": {
                "note": "Totals of mapped power plant sites above each type's MW threshold (WRI Global Power Plant Database).",
                "national": nat_sum,
                "states": st_sum,
            },
        },
    )
