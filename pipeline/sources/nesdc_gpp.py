"""NESDC Gross Regional and Provincial Product (GPP) 1995–2024 (all 77 provinces, 16 ISIC sectors).

Parses the official Excel workbook published by Thailand's Office of the National
Economic and Social Development Council (NESDC) using Python's standard library only
(zipfile + xml.etree.ElementTree).
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from ..core.source import Source, SourceInfo
from ..core.thailand import BY_CODE, resolve_province

GPP_URL = "https://www.nesdc.go.th/wp-content/uploads/2026/03/GPP-2024-On-Web-1995-2024.xlsx"

# Canonical mapping from NESDC row labels (lowercase substring match) → industry key
SECTOR_MAP = [
    ("agriculture, forestry and fishing", "agriculture"),
    ("mining and quarrying", "mining"),
    ("manufacturing", "manufacturing"),
    ("electricity, gas, steam", "utilities"),
    ("water supply; sewerage", "water_waste"),
    ("construction", "construction"),
    ("wholesale and retail trade", "trade"),
    ("transportation and storage", "transportation"),
    ("accommodation and food service", "accommodation"),
    ("information and communication", "information"),
    ("financial and insurance", "finance"),
    ("real estate activities", "real_estate"),
    ("professional, scientific and technical", "professional"),
    ("administrative and support service", "admin"),
    ("public administration and defence", "public_admin"),
    ("education", "education"),
    ("human health and social work", "health"),
    ("arts, entertainment and recreation", "arts"),
    ("other service activities", "other"),
]

PROVINCE_SHEETS = ("NE", "NO", "SO", "EA", "WE", "CE", "BKK&VIC")


def _col_idx(ref: str) -> int:
    col = "".join(ch for ch in ref if ch.isalpha())
    n = 0
    for ch in col:
        n = n * 26 + (ord(ch.upper()) - ord("A") + 1)
    return n - 1


def _parse_xlsx_sheets(path: Path) -> dict[str, list[dict[int, str]]]:
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as zf:
        ss: list[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            for si in root.findall("m:si", ns):
                ss.append("".join(t.text or "" for t in si.iter("{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t")))
        wb = ET.fromstring(zf.read("xl/workbook.xml"))
        rels = ET.fromstring(zf.read("xl/_rels/workbook.xml.rels"))
        rmap = {r.attrib["Id"]: r.attrib["Target"] for r in rels}
        out: dict[str, list[dict[int, str]]] = {}
        for s in wb.findall(".//m:sheet", ns):
            name = s.attrib["name"]
            if name not in ("WK",) + PROVINCE_SHEETS:
                continue
            rid = s.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
            target = "xl/" + rmap[rid].lstrip("/")
            root = ET.fromstring(zf.read(target))
            rows = []
            for row in root.findall(".//m:sheetData/m:row", ns):
                rm: dict[int, str] = {}
                for c in row.findall("m:c", ns):
                    t = c.attrib.get("t", "")
                    v = c.find("m:v", ns)
                    if v is None or v.text is None:
                        continue
                    val = ss[int(v.text)] if t == "s" else v.text
                    rm[_col_idx(c.attrib["r"])] = val.strip()
                if rm:
                    rows.append(rm)
            out[name] = rows
        return out


def _num(s: str | None) -> float | None:
    if s is None or s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _parse_block(rows: list[dict[int, str]], start_idx: int, end_idx: int) -> dict | None:
    """Parse one Current Market Prices block (header + year row + sector rows + totals)."""
    # Find year header row (has 1995..2024p/2023r)
    year_cols: dict[int, int] = {}
    year_row_idx = start_idx
    for i in range(start_idx, min(end_idx, start_idx + 10)):
        for c, val in rows[i].items():
            m = re.match(r"^(199\d|20[0-2]\d)[pr]?$", val.strip(), re.I)
            if m:
                year_cols[int(m.group(1))] = c
        if len(year_cols) >= 10:
            year_row_idx = i
            break
    if not year_cols:
        return None
    latest_year = max(year_cols)
    ycol = year_cols[latest_year]

    sectors: dict[str, float] = {}
    gpp_mthb: float | None = None
    gpp_series: dict[str, float] = {}
    per_cap: float | None = None
    pop_k: float | None = None
    pop_series_k: dict[str, float] = {}

    for i in range(year_row_idx + 1, end_idx):
        lbl = (rows[i].get(0) or "").strip()
        if not lbl:
            continue
        low = lbl.lower()
        # Stop immediately if the stacked Chain Volume Measures table begins!
        if "chain volume" in low or "(cvms)" in low:
            break
        val = _num(rows[i].get(ycol))
        if low.startswith("gross provincial product") or low.startswith("gross domestic product"):
            if val is not None and gpp_mthb is None:
                gpp_mthb = val
                for yr in sorted(year_cols):
                    if yr >= 2015:
                        v = _num(rows[i].get(year_cols[yr]))
                        if v is not None:
                            gpp_series[str(yr)] = round(v * 1e6)
            continue
        if "per capita" in low:
            if val is not None and per_cap is None:
                per_cap = val
            continue
        if low.startswith("population"):
            if val is not None and pop_k is None:
                pop_k = val
                for yr in sorted(year_cols):
                    if yr >= 2015:
                        v = _num(rows[i].get(year_cols[yr]))
                        if v is not None:
                            pop_series_k[str(yr)] = round(v * 1000)
            continue
        for pat, key in SECTOR_MAP:
            if low.startswith(pat):
                if val is not None and key not in sectors:
                    sectors[key] = round(val * 1e6)
                break

    if gpp_mthb is None:
        return None
    # Merge water_waste into utilities (matching standard utility sector) while preserving water_waste too
    return {
        "year": latest_year,
        "gpp_thb": round(gpp_mthb * 1e6),
        "gpp_per_capita_thb": round(per_cap) if per_cap is not None else None,
        "nesdc_pop": round(pop_k * 1000) if pop_k is not None else None,
        "gpp_series_thb": gpp_series,
        "pop_series": pop_series_k,
        "sectors_thb": sectors,
    }


class NesdcGpp(Source):
    info = SourceInfo(
        id="nesdc_gpp",
        title="Gross Regional and Provincial Product (GPP) 1995–2024",
        publisher="Office of the National Economic and Social Development Council (NESDC)",
        homepage="https://www.nesdc.go.th/",
        license="Thai Government Open Data",
        description="Official current-price Gross Provincial Product (THB), GPP per capita, and 19-sector economic output for all 77 provinces of Thailand (1995–2024p).",
        used_for=["Gold yield (GPP)", "Industry GDP breakdown", "City specialization districts & badges", "Economic lenses"],
    )

    def fetch(self, force: bool = False) -> None:
        self.download(GPP_URL, "GPP-2024-On-Web-1995-2024.xlsx", force=force, expect_binary=True)

    def process(self) -> dict:
        sheets = _parse_xlsx_sheets(self.raw_dir / "GPP-2024-On-Web-1995-2024.xlsx")
        wk_rows = sheets["WK"]
        national = _parse_block(wk_rows, 0, len(wk_rows))

        provinces: dict[str, dict] = {}
        for sh in PROVINCE_SHEETS:
            rows = sheets.get(sh) or []
            # Each province block begins with a row where col 0 matches "0401 - CHON BURI" or "GROSS PROVINCIAL PRODUCT"
            starts: list[tuple[int, str]] = []
            for i, rm in enumerate(rows):
                a = rm.get(0, "")
                if re.match(r"^\d{4}\s*[-–]\s*\S+", a):
                    code = resolve_province(a)
                    if code:
                        starts.append((i, code))
            for k, (idx, code) in enumerate(starts):
                # Skip the second (Chain Volume Measures) block for a province already parsed at Current Market Prices!
                prev_hdr = (rows[idx - 1].get(0) or "").upper() if idx > 0 else ""
                if "CHAIN VOLUME" in prev_hdr or code in provinces:
                    continue
                end = starts[k + 1][0] if k + 1 < len(starts) else len(rows)
                parsed = _parse_block(rows, idx, end)
                if parsed:
                    provinces[code] = parsed

        year = national["year"] if national else 2024
        return {
            "vintage": f"NESDC GPP {year}p (1995–{year})",
            "year": year,
            "national": national,
            "provinces": provinces,
            "_files": ["GPP-2024-On-Web-1995-2024.xlsx"],
        }
