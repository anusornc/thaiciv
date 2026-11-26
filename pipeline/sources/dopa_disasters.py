"""DOPA 76-Province Village Disaster Risk Records (catalog.dopa.go.th)."""

from __future__ import annotations

import json

from ..core.source import Source, SourceInfo
from ..core.thailand import resolve_province

DOPA_DISASTER_URL = (
    "https://catalog.dopa.go.th/dataset/c667e7aa-2e62-4c43-a8e1-dd78cfc0758c"
    "/resource/13cf6543-82fb-4632-a9d4-7df43f391bac/download/untitled.json"
)

# DOPA type_disaster_id mapping (Thai village hazard reporting codes)
# 1: Flood, 2: Drought, 3: Windstorm/Severe Storm, 4: Cold spell, 5: Fire/Wildfire,
# 6: Landslide/Mudslide, 7: Earthquake, 8: Flood/Storm/Other
TYPE_MAP = {
    "1": "flood",
    "2": "drought",
    "3": "severe_storm",
    "4": "other",
    "5": "fire",
    "6": "landslide",
    "7": "other",
    "8": "flood",
}


class DopaDisasters(Source):
    info = SourceInfo(
        id="dopa_disasters",
        title="Village-Level Disaster Risk & Hazard Database (76 Provinces)",
        publisher="Department of Provincial Administration (DOPA), Ministry of Interior",
        homepage="https://catalog.dopa.go.th/",
        license="Thai Government Open Data",
        description="Official village-level disaster hazard reports across 76 provinces (outside Bangkok) recording flood, drought, storm, fire and landslide exposure by district (amphoe).",
        used_for=["Disasters lens", "Hazards & Disasters advisor", "District-level hazard exposure"],
    )

    def fetch(self, force: bool = False) -> None:
        self.download(DOPA_DISASTER_URL, "dopa_disasters.json", force=force)

    def process(self) -> dict:
        raw = json.loads((self.raw_dir / "dopa_disasters.json").read_text(encoding="utf-8-sig", errors="replace"))
        by_prov: dict[str, dict] = {}
        by_dist: dict[str, dict] = {}
        years: set[int] = set()

        for r in raw:
            code = resolve_province(r.get("pcode")) or resolve_province(r.get("pname"))
            if not code:
                continue
            tid = str(r.get("type_disaster_id") or "").strip()
            cat = TYPE_MAP.get(tid, "other")
            dy = str(r.get("d_year") or "").strip()
            if dy.isdigit():
                y = int(dy)
                years.add(y - 543 if y > 2400 else y)

            pr = by_prov.setdefault(code, {"total": 0, "by_type": {}})
            pr["total"] += 1
            pr["by_type"][cat] = pr["by_type"].get(cat, 0) + 1

            aname = (r.get("aname") or "").strip()
            if aname:
                dk = f"{code}:{aname}"
                dr = by_dist.setdefault(dk, {"province": code, "th_name": aname, "total": 0, "by_type": {}})
                dr["total"] += 1
                dr["by_type"][cat] = dr["by_type"].get(cat, 0) + 1

        y0, y1 = (min(years), max(years)) if years else (2020, 2024)
        return {
            "vintage": f"DOPA Village Disaster Risk ({y0}–{y1})",
            "years": [y0, y1],
            "total_records": len(raw),
            "provinces": by_prov,
            "districts_th": list(by_dist.values()),
            "_files": ["dopa_disasters.json"],
        }
