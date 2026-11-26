"""Thailand surface-water Arsenic (As), Lead (Pb) & Manganese (Mn) monitoring data (Chiang Rai Open Data / PCD)."""

from __future__ import annotations

import csv
import re

from ..core.source import Source, SourceInfo

CR_MONITORING_URL = (
    "https://chiangrai.gdcatalog.go.th/dataset/e1fc8a4f-1d5c-4571-aff2-89a35e554a08"
    "/resource/fb5ba42e-1600-4dc0-9b86-97bba09c49c7/download/untitled.csv"
)
CR_BASELINE_URL = (
    "https://chiangrai.gdcatalog.go.th/dataset/2e5aa282-25db-460c-ac6d-d38c4e1bf468"
    "/resource/80b328f4-2871-4b1c-bfca-d5414c25d756/download/h2o_cr.csv"
)

THAI_MONTHS = {
    "มกราคม": 1, "กุมภาพันธ์": 2, "มีนาคม": 3, "เมษายน": 4,
    "พฤษภาคม": 5, "มิถุนายน": 6, "กรกฎาคม": 7, "สิงหาคม": 8,
    "กันยายน": 9, "ตุลาคม": 10, "พฤศจิกายน": 11, "ธันวาคม": 12,
}


def _parse_measurement(raw: str | None) -> dict | None:
    """Parse lab value: '0' → not sampled in round (None); '<0.010' → below detection limit; float → measured."""
    if raw is None:
        return None
    s = raw.strip()
    if not s or s == "0" or s == "-":
        return None
    if s.startswith("<"):
        try:
            dl = float(s[1:].strip())
        except ValueError:
            return None
        return {"raw": s, "val": round(dl * 0.5, 5), "dl": dl, "below_dl": True}
    try:
        v = float(s)
    except ValueError:
        return None
    return {"raw": s, "val": v, "dl": None, "below_dl": False}


class ArsenicThailand(Source):
    info = SourceInfo(
        id="arsenic_thailand",
        title="Surface Water Arsenic & Heavy Metal Monitoring (Kok, Sai, Ruak, Mekong & Tributaries)",
        publisher="Chiang Rai Provincial Office / Pollution Control Department (PCD) / Chiang Rai PHO (via data.go.th)",
        homepage="https://chiangrai.gdcatalog.go.th/dataset/e1fc8a4f-1d5c-4571-aff2-89a35e554a08",
        license="Thai Government Open Data (data.go.th)",
        description="Official multi-round surface water monitoring of Arsenic (As), Lead (Pb), and Manganese (Mn) across 23 stations on the Kok, Sai, Ruak, Mekong rivers and Thai-origin control tributaries (Lao, Suai, Korn), plus 2017–2025 historical baseline at Kok River KK01.",
        used_for=["Arsenic map layer", "Arsenic (As) hazard lens", "Water & Arsenic advisor dashboard"],
    )

    def fetch(self, force: bool = False) -> None:
        self.download(CR_MONITORING_URL, "kok_sai_monitoring.csv", force=force)
        self.download(CR_BASELINE_URL, "kok_baseline_2017_2025.csv", force=force)

    def process(self) -> dict:
        stations_map: dict[str, dict] = {}
        with open(self.raw_dir / "kok_sai_monitoring.csv", encoding="utf-8-sig", errors="replace") as f:
            for row in csv.DictReader(f):
                st_id = (row.get("สถานี") or "").strip()
                if not st_id:
                    continue
                river_th = (row.get("แม่น้ำ") or "").strip()
                loc_th = (row.get("บริเวณจุดเก็บ") or "").strip()
                rnd_s = (row.get("ครั้งที่") or "").strip()
                rnd = int(rnd_s) if rnd_s.isdigit() else 0
                source_th = (row.get("ที่มา") or "").strip()

                rec = stations_map.setdefault(
                    st_id,
                    {
                        "id": st_id,
                        "river_th": river_th,
                        "location_th": loc_th,
                        "source_th": source_th,
                        "rounds": [],
                    },
                )
                as_m = _parse_measurement(row.get("As"))
                pb_m = _parse_measurement(row.get("Pb"))
                mn_m = _parse_measurement(row.get("Mn"))
                rec["rounds"].append({
                    "round": rnd,
                    "as": as_m,
                    "pb": pb_m,
                    "mn": mn_m,
                })

        for rec in stations_map.values():
            rec["rounds"].sort(key=lambda x: x["round"])

        baseline = []
        with open(self.raw_dir / "kok_baseline_2017_2025.csv", encoding="utf-8-sig", errors="replace") as f:
            for row in csv.DictReader(f):
                yr_s = (row.get("ปี") or "").strip()
                if not yr_s.isdigit():
                    continue
                yr_be = int(yr_s)
                yr_ce = yr_be - 543 if yr_be > 2400 else yr_be
                m_th = (row.get("เดือน") or "").strip()
                m_num = THAI_MONTHS.get(m_th, 1)
                try:
                    val = float((row.get("ค่าข้อมูล") or "").strip())
                except ValueError:
                    continue
                baseline.append({
                    "year_be": yr_be,
                    "year": yr_ce,
                    "month": m_num,
                    "month_th": m_th,
                    "date": f"{yr_ce}-{m_num:02d}",
                    "station": (row.get("สถานีตรวจวัด") or "KK01").strip(),
                    "as_mg_l": round(val, 4),
                    "source": (row.get("ที่มา") or "").strip(),
                })
        baseline.sort(key=lambda x: (x["year"], x["month"]))

        return {
            "vintage": "Chiang Rai / PCD 8-Round Monitoring (2025–2026) & Baseline 2017–2025",
            "standard_as_mg_l": 0.01,
            "standard_pb_mg_l": 0.05,
            "standard_mn_mg_l": 1.0,
            "stations": sorted(stations_map.values(), key=lambda x: x["id"]),
            "baseline": baseline,
            "_files": ["kok_sai_monitoring.csv", "kok_baseline_2017_2025.csv"],
        }
