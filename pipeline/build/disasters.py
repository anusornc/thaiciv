"""Build disasters.json from DOPA 76-Province Village Disaster Risk Records."""

from __future__ import annotations

from ..core.store import load_interim, save_web
from ..core.thailand import BY_CODE

REQUIRES = ["thailand_boundaries", "dopa_disasters"]
PRODUCES = ["disasters.json"]

TYPES = [
    {"id": "flood", "name": "Flooding & flash floods", "incident_types": ["Flood"]},
    {"id": "drought", "name": "Drought & dry spells", "incident_types": ["Drought"]},
    {"id": "severe_storm", "name": "Tropical storms & windstorms", "incident_types": ["Storm"]},
    {"id": "fire", "name": "Wildfire & haze", "incident_types": ["Fire"]},
    {"id": "landslide", "name": "Landslides & mudslides", "incident_types": ["Landslide"]},
    {"id": "other", "name": "Cold spells & other hazards", "incident_types": []},
]


def build() -> None:
    tb = load_interim("thailand_boundaries")
    dis = load_interim("dopa_disasters")

    y0, y1 = dis.get("years") or [2020, 2024]
    states_out = {}
    for code, rec in dis.get("provinces", {}).items():
        if code not in BY_CODE:
            continue
        abbr = BY_CODE[code][1]
        bt = {t["id"]: rec["by_type"].get(t["id"], 0) for t in TYPES}
        states_out[abbr] = {"total": rec["total"], "statewide": 0, "by_type": bt}

    # District rows aligned with world.json counties order
    c_rows = []
    for d in tb["districts"]:
        pcode = d["state_fips"]
        rec = dis.get("provinces", {}).get(pcode)
        if not rec:
            c_rows.append([d["geoid"], 0, 0, 0, 0, 0, 0, 0, None])
        else:
            bt = rec["by_type"]
            c_rows.append([
                d["geoid"],
                rec["total"],
                bt.get("flood", 0),
                bt.get("drought", 0),
                bt.get("severe_storm", 0),
                bt.get("fire", 0),
                bt.get("landslide", 0),
                bt.get("other", 0),
                f"{y1}-12-31",
            ])

    save_web(
        "disasters.json",
        {
            "version": 1,
            "sources": ["dopa_disasters"],
            "vintage": {"fema": dis.get("vintage", "DOPA Village Disaster Risk"), "noaa": "Not applicable (Thailand DOPA village hazard records)"},
            "fema": {
                "window": [f"{y0}-01-01", f"{y1}-12-31"],
                "as_of": f"{y1}-12-31",
                "rule": "Official village-level hazard reports (flood, drought, windstorm, fire, landslide) collected across 76 provinces by Thailand's Department of Provincial Administration (DOPA). Bangkok is not part of the rural village survey.",
                "types": TYPES,
                "counties": {
                    "columns": ["geoid", "total", "flood", "drought", "severe_storm", "fire", "landslide", "other", "last_date"],
                    "rows": c_rows,
                },
                "states": states_out,
                "recent_days": 365,
                "recent": [],
            },
            "noaa": None,
        },
    )
