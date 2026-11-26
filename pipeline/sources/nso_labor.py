"""NSO Labor Force Survey (77 provinces) plus regional internet & religion context."""

from __future__ import annotations

import csv

from ..core.source import Source, SourceInfo
from ..core.thailand import resolve_province

NSO_BASE = "https://catalogapi.nso.go.th/api/index?table={table}&format=csv"

TABLES = {
    "labor_force": "ST_02_2005005_4",        # 77-province labor force status (employed, unemployed, seasonal)
    "internet_hh": "ICTH_37_24_Table_25per", # Regional household internet access %
    "religion_reg": "OS_04_0001_01",         # Regional religion survey counts
}


def _to_float(v: str | None) -> float | None:
    if v is None:
        return None
    s = v.strip().replace(",", "")
    if not s or s in ("-", ".."):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _be_to_ce(y: str | None) -> int | None:
    if not y:
        return None
    s = y.strip()
    if not s.isdigit():
        return None
    n = int(s)
    return n - 543 if n > 2400 else n


class NsoLabor(Source):
    info = SourceInfo(
        id="nso_labor",
        title="Labor Force Survey (77 Provinces), Household Internet & Religion Survey",
        publisher="National Statistical Office of Thailand (NSO)",
        homepage="https://www.nso.go.th/",
        license="Thai Government Open Data (data.go.th)",
        description="Official provincial labor force, employed and unemployed worker counts from the NSO Labor Force Survey, plus regional internet connectivity and religion statistics.",
        used_for=["Employment & unemployment by province", "Workforce totals", "Broadband/internet & faith context"],
    )

    def fetch(self, force: bool = False) -> None:
        for name, tbl in TABLES.items():
            self.download(NSO_BASE.format(table=tbl), f"{name}.csv", force=force)

    def process(self) -> dict:
        # 1. ST_02_2005005_4: YEAR,QUARTER,REGION,PROVINCE,SEX,LABOR_FORCE_STATUS,VALUE,UNIT,SOURCE
        # Find latest year available, average across quarters within that year, sum across sex!
        rows_by_yr: dict[int, list[dict]] = {}
        with open(self.raw_dir / "labor_force.csv", encoding="utf-8-sig", errors="replace") as f:
            for row in csv.DictReader(f):
                yr = _be_to_ce(row.get("YEAR") or row.get("year"))
                if not yr:
                    continue
                rows_by_yr.setdefault(yr, []).append(row)

        latest_yr = max(rows_by_yr) if rows_by_yr else 2024
        # Aggregate per (province, quarter, status) summing male+female (or taking "รวม" if present)
        by_pq: dict[tuple[str, str], dict[str, float]] = {}
        has_total_sex = any((r.get("SEX") or "").strip() == "รวม" for r in rows_by_yr.get(latest_yr, []))

        for row in rows_by_yr.get(latest_yr, []):
            sex = (row.get("SEX") or "").strip()
            if has_total_sex and sex != "รวม":
                continue
            if not has_total_sex and sex not in ("ชาย", "หญิง"):
                continue
            code = resolve_province(row.get("PROVINCE"))
            if not code:
                continue
            q = (row.get("QUARTER") or "Q1").strip()
            st = (row.get("LABOR_FORCE_STATUS") or "").strip()
            val = _to_float(row.get("VALUE"))
            if val is None:
                continue
            unit = (row.get("UNIT") or "").strip()
            mult = 1000.0 if "พัน" in unit else 1.0
            d = by_pq.setdefault((code, q), {})
            if "มีงานทำ" in st:
                d["employed"] = d.get("employed", 0.0) + val * mult
            elif "ว่างงาน" in st:
                d["unemployed"] = d.get("unemployed", 0.0) + val * mult
            elif "รอฤดูกาล" in st:
                d["seasonal"] = d.get("seasonal", 0.0) + val * mult

        # Average across quarters per province
        provinces: dict[str, dict] = {}
        by_p: dict[str, list[dict[str, float]]] = {}
        for (code, _q), d in by_pq.items():
            by_p.setdefault(code, []).append(d)
        for code, qs in by_p.items():
            emp = round(sum(d.get("employed", 0.0) for d in qs) / len(qs))
            unemp = round(sum(d.get("unemployed", 0.0) for d in qs) / len(qs))
            lf = emp + unemp
            rate = round(unemp / lf, 4) if lf > 0 else None
            provinces[code] = {
                "employed": emp,
                "unemployed": unemp,
                "labor_force": lf,
                "unemployment_rate": rate,
            }

        # 2. Regional household internet access % (latest year)
        internet_reg: dict[str, float] = {}
        best_inet_yr = 0
        inet_rows = []
        with open(self.raw_dir / "internet_hh.csv", encoding="utf-8-sig", errors="replace") as f:
            for row in csv.DictReader(f):
                yr = _be_to_ce(row.get("year"))
                area = (row.get("area") or "").strip()
                if not yr or area not in ("รวม", ""):
                    continue
                if yr > best_inet_yr:
                    best_inet_yr = yr
                inet_rows.append((yr, (row.get("region") or "").strip(), _to_float(row.get("Per_connect"))))
        for yr, reg, val in inet_rows:
            if yr == best_inet_yr and val is not None:
                internet_reg[reg] = round(val / 100.0, 4)

        # 3. Regional religion counts (latest year)
        rel_reg: dict[str, dict[str, float]] = {}
        best_rel_yr = 0
        rel_rows = []
        with open(self.raw_dir / "religion_reg.csv", encoding="utf-8-sig", errors="replace") as f:
            for row in csv.DictReader(f):
                yr = _be_to_ce(row.get("year"))
                sex = (row.get("sex") or "").strip()
                if not yr or sex not in ("รวม", ""):
                    continue
                if yr > best_rel_yr:
                    best_rel_yr = yr
                rel_rows.append((yr, (row.get("region") or "").strip(), (row.get("religion") or "").strip(), _to_float(row.get("value"))))
        for yr, reg, rel, val in rel_rows:
            if yr == best_rel_yr and val is not None:
                rel_reg.setdefault(reg, {})[rel] = val

        return {
            "vintage": f"NSO Labor Force Survey {latest_yr} & ICT {best_inet_yr}",
            "year": latest_yr,
            "provinces": provinces,
            "internet_by_region": internet_reg,
            "internet_year": best_inet_yr,
            "religion_by_region": rel_reg,
            "religion_year": best_rel_yr,
            "_files": [f"{k}.csv" for k in TABLES],
        }
