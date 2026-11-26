"""DOPA Civil Registration population: 77 provinces (2020–2025) & 928 districts (amphoe)."""

from __future__ import annotations

import json
from pathlib import Path

from ..core.source import Source, SourceInfo
from ..core.thailand import resolve_province

DOPA_API = (
    "https://stat.bora.dopa.go.th/stat/statnew/connectSAPI/stat_forward.php"
    "?API=/api/statpophouse/v1/statpop/list?action=41&yymmBegin={yymm}&yymmEnd={yymm}"
    "&statType=0&statSubType=999&subType=99"
)
# Official DOPA district population dump on data.go.th
DOPA_DISTRICT_URL = (
    "https://data.go.th/dataset/c6fb53a5-4d9d-4f21-84a7-9662b25af9c3"
    "/resource/7158388c-237a-4fa3-9fc2-a27a0cf6fda5/download/stat_a.txt"
)

# Buddhist Era YYMM (December) → Gregorian Year
YEARS = [
    ("6312", "2020"),
    ("6412", "2021"),
    ("6512", "2022"),
    ("6612", "2023"),
    ("6712", "2024"),
    ("6812", "2025"),
]


class DopaPopulation(Source):
    info = SourceInfo(
        id="dopa_population",
        title="Civil Registration Population Statistics (77 Provinces & 928 Districts)",
        publisher="Department of Provincial Administration (DOPA), Ministry of Interior",
        homepage="https://stat.bora.dopa.go.th/",
        license="Thai Government Open Data",
        description="Official year-end registered population (total, male, female, Thai and non-Thai nationals) for all 77 provinces (2020–2025) plus district-level (amphoe) population and households.",
        used_for=["Provincial population & 2021–2025 growth", "Population time series", "Non-Thai resident share", "District (amphoe) population & density"],
    )

    def fetch(self, force: bool = False) -> None:
        for yymm, yr in YEARS:
            self.download(DOPA_API.format(yymm=yymm), f"prov_{yr}.json", force=force)
        self.download(DOPA_DISTRICT_URL, "stat_a.txt", force=force)

    def process(self) -> dict:
        provinces: dict[str, dict] = {}
        used_files: list[str] = []

        for _, yr in YEARS:
            fn = f"prov_{yr}.json"
            p = self.raw_dir / fn
            if not p.exists():
                continue
            rows = json.loads(p.read_text(encoding="utf-8"))
            used_files.append(fn)
            for r in rows:
                code = resolve_province(r.get("lscc")) or resolve_province(r.get("lsccDesc"))
                if not code:
                    continue
                rec = provinces.setdefault(code, {"series": {}, "thai": None, "non_thai": None, "male": None, "female": None})
                tot = int(r.get("lssumtotTot") or 0)
                thai = int(r.get("lssumtotTotThai") or 0)
                male = int(r.get("lssumtotMale") or 0)
                female = int(r.get("lssumtotFemale") or 0)
                rec["series"][yr] = tot
                if yr == YEARS[-1][1]:
                    rec["population"] = tot
                    rec["thai"] = thai
                    rec["non_thai"] = max(0, tot - thai)
                    rec["male"] = male
                    rec["female"] = female

        # District-level (amphoe) population from stat_a.txt (pipe-delimited)
        # Keep the latest YYMM available in stat_a.txt per amphoe!
        districts: dict[str, dict] = {}
        dist_path = self.raw_dir / "stat_a.txt"
        if dist_path.exists():
            used_files.append("stat_a.txt")
            latest_ym = 0
            raw_rows = []
            with open(dist_path, encoding="utf-8-sig", errors="replace") as f:
                header = f.readline()
                for line in f:
                    parts = line.strip().split("|")
                    if len(parts) < 13:
                        continue
                    ym = int(parts[0]) if parts[0].isdigit() else 0
                    cc = parts[1].strip()
                    rc = parts[3].strip()
                    rc_desc = parts[4].strip()
                    if cc == "0" or rc == "0" or not rc_desc:
                        continue
                    if ym > latest_ym:
                        latest_ym = ym
                    raw_rows.append((ym, cc, rc, rc_desc, parts[9], parts[10], parts[11], parts[12]))
            for ym, cc, rc, rc_desc, sm, sf, st, sh in raw_rows:
                if ym != latest_ym:
                    continue
                code = resolve_province(cc)
                if not code:
                    continue
                try:
                    pop = int(st.replace(",", ""))
                    house = int(sh.replace(",", ""))
                except ValueError:
                    continue
                # Normalize amphoe name (strip "อำเภอ" / "เขต" / "ท้องถิ่น...")
                key = f"{code}:{rc_desc}"
                cur = districts.get(key)
                if cur is None:
                    districts[key] = {
                        "province": code,
                        "rcode": rc,
                        "th_name": rc_desc,
                        "population": pop,
                        "houses": house,
                    }
                else:
                    cur["population"] += pop
                    cur["houses"] += house

        return {
            "vintage": "DOPA Civil Registration (Dec 2020 – Dec 2025)",
            "year": 2025,
            "provinces": provinces,
            "districts_th": list(districts.values()),
            "_files": used_files,
        }
