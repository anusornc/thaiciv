"""NSO Household Socio-Economic Survey (SES) & Census indicators by province (catalogapi.nso.go.th)."""

from __future__ import annotations

import csv

from ..core.source import Source, SourceInfo
from ..core.thailand import resolve_province

NSO_BASE = "https://catalogapi.nso.go.th/api/index?table={table}&format=csv"

TABLES = {
    "income": "SFD_SPB0802_66",       # Monthly household income by province (up to 2568 / 2025)
    "expense": "SFD_SPB0802_67",      # Monthly household expenditure by province (up to 2567 / 2024)
    "debt": "SFD_SPB0806",            # Average household debt by province (up to 2566 / 2023)
    "summary": "SFD_SPB0801",         # Monthly income, expenditure, debt, exp/inc % by province (2568)
    "homeownership": "OS_01_00059_01",# Homeownership % by province
    "migration": "OS_01_00033_01",    # % population not living in birth province
    "establishments": "SFD_SPB1201",  # Business & Industrial Census establishments by province
}


def _to_float(v: str | None) -> float | None:
    if v is None:
        return None
    s = v.strip().replace(",", "")
    if not s or s in ("-", "..", "N/A", "null"):
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


class NsoSes(Source):
    info = SourceInfo(
        id="nso_ses",
        title="Household Socio-Economic Survey (SES) & Business Census by Province",
        publisher="National Statistical Office of Thailand (NSO)",
        homepage="https://www.nso.go.th/",
        license="Thai Government Open Data (data.go.th)",
        description="Official provincial statistics on monthly household income, expenditure, debt, expenditure-to-income ratio, homeownership, internal migration and registered business establishments.",
        used_for=["Household income, expenditure & debt lenses", "City & province prosperity panels", "Homeownership & migration lenses", "Establishments per capita"],
    )

    def fetch(self, force: bool = False) -> None:
        for name, tbl in TABLES.items():
            self.download(NSO_BASE.format(table=tbl), f"{name}.csv", force=force)

    def process(self) -> dict:
        provinces: dict[str, dict] = {}
        national: dict = {}
        years: dict[str, int] = {}

        def _rec(code: str) -> dict:
            return provinces.setdefault(code, {})

        # 1. SFD_SPB0801 (summary: income, expense, debt, exp_to_income_pct — latest BE year per province!)
        # Also extracts socio-economic class breakdown for Citizens panel!
        best_yr_sum: dict[tuple[str, str], int] = {}
        ses_classes: dict[str, dict[str, float]] = {}
        with open(self.raw_dir / "summary.csv", encoding="utf-8-sig", errors="replace") as f:
            for row in csv.DictReader(f):
                yr = _be_to_ce(row.get("year"))
                if not yr:
                    continue
                prov_raw = (row.get("province") or "").strip()
                metric = (row.get("mthincome_mthexp_totaldebt_pctexptoincome") or "").strip()
                c1 = (row.get("soc_eco_class1") or "").strip()
                c2 = (row.get("soc_eco_class2") or "").strip()
                val = _to_float(row.get("value"))
                if val is None:
                    continue
                code = resolve_province(prov_raw)
                is_nat = prov_raw in ("ทั่วประเทศ", "ทั่วราชอาณาจักร", "รวม")
                if not code and not is_nat:
                    continue
                # Total row: soc_eco_class1 == "รวมทั้งสิ้น" or "รวม"
                is_total = ("รวม" in c1 and ("รวม" in c2 or c2 == "")) or (c1 == c2 and "รวม" in c1)
                if not is_total:
                    continue
                key = None
                if "รายได้" in metric and "ร้อยละ" not in metric and "สัดส่วน" not in metric:
                    key = "monthly_income_thb"
                elif "ค่าใช้จ่าย" in metric and "ร้อยละ" not in metric and "สัดส่วน" not in metric:
                    key = "monthly_expense_thb"
                elif "หนี้สิน" in metric:
                    key = "household_debt_thb"
                elif "ร้อยละ" in metric or "ต่อรายได้" in metric:
                    key = "expense_to_income_pct"
                if not key:
                    continue
                target = "NAT" if is_nat else code
                if yr >= best_yr_sum.get((target, key), 0):
                    best_yr_sum[(target, key)] = yr
                    years[key] = max(years.get(key, 0), yr)
                    if is_nat:
                        national[key] = val
                    else:
                        _rec(code)[key] = val

        # 2. Fallback/supplement monthly income from SFD_SPB0802_66 (if SFD_SPB0801 missed any province)
        best_inc: dict[str, int] = {}
        with open(self.raw_dir / "income.csv", encoding="utf-8-sig", errors="replace") as f:
            for row in csv.DictReader(f):
                yr = _be_to_ce(row.get("year"))
                if not yr:
                    continue
                s1 = (row.get("source_income1") or "").strip()
                s2 = (row.get("source_income2") or "").strip()
                s3 = (row.get("source_income3") or "").strip()
                c1 = (row.get("soc_eco_class1") or "").strip()
                c2 = (row.get("soc_eco_class2") or "").strip()
                if "รายได้ทั้งสิ้น" in s1 and "รวม" in c1 and ("รวม" in c2 or not c2):
                    val = _to_float(row.get("value"))
                    code = resolve_province(row.get("province"))
                    if code and val is not None and yr >= best_inc.get(code, 0):
                        best_inc[code] = yr
                        _rec(code).setdefault("monthly_income_thb", val)
                        years["monthly_income_thb"] = max(years.get("monthly_income_thb", 0), yr)

        # 3. Monthly expense fallback from SFD_SPB0802_67
        best_exp: dict[str, int] = {}
        with open(self.raw_dir / "expense.csv", encoding="utf-8-sig", errors="replace") as f:
            for row in csv.DictReader(f):
                yr = _be_to_ce(row.get("year"))
                if not yr:
                    continue
                t1 = (row.get("type_expenditure1") or "").strip()
                t2 = (row.get("type_expenditure2") or "").strip()
                iv = (row.get("Intervals_monthly_exp_hh") or "").strip()
                if "ค่าใช้จ่ายทั้งสิ้น" in t1 and t1 == t2 and "รวม" in iv:
                    val = _to_float(row.get("value"))
                    code = resolve_province(row.get("province"))
                    if code and val is not None and yr >= best_exp.get(code, 0):
                        best_exp[code] = yr
                        _rec(code).setdefault("monthly_expense_thb", val)
                        years["monthly_expense_thb"] = max(years.get("monthly_expense_thb", 0), yr)

        # 4. Household debt fallback from SFD_SPB0806
        best_debt: dict[str, int] = {}
        with open(self.raw_dir / "debt.csv", encoding="utf-8-sig", errors="replace") as f:
            for row in csv.DictReader(f):
                yr = _be_to_ce(row.get("year"))
                if not yr:
                    continue
                c1 = (row.get("soc_eco_class1") or "").strip()
                c2 = (row.get("soc_eco_class2") or "").strip()
                d1 = (row.get("hhdebt_totaldebt") or "").strip()
                d2 = (row.get("hhdebt_totaldebt_purpose_source") or "").strip()
                if "รวม" in c1 and ("รวม" in c2 or not c2) and "หนี้สินทั้งสิ้น" in d1 and ("รวม" in d2 or d1 == d2):
                    val = _to_float(row.get("value"))
                    code = resolve_province(row.get("province"))
                    if code and val is not None and yr >= best_debt.get(code, 0):
                        best_debt[code] = yr
                        _rec(code).setdefault("household_debt_thb", val)
                        years["household_debt_thb"] = max(years.get("household_debt_thb", 0), yr)

        # 5. Homeownership % (OS_01_00059_01)
        best_ho: dict[str, int] = {}
        with open(self.raw_dir / "homeownership.csv", encoding="utf-8-sig", errors="replace") as f:
            for row in csv.DictReader(f):
                yr = _be_to_ce(row.get("year"))
                val = _to_float(row.get("value"))
                if not yr or val is None:
                    continue
                pr = (row.get("province") or "").strip()
                if pr in ("รวม", "ทั่วประเทศ", "ทั่วราชอาณาจักร"):
                    if yr >= best_ho.get("NAT", 0):
                        best_ho["NAT"] = yr
                        national["homeownership"] = round(val / 100.0, 4)
                    continue
                code = resolve_province(pr)
                if code and yr >= best_ho.get(code, 0):
                    best_ho[code] = yr
                    _rec(code)["homeownership"] = round(val / 100.0, 4)

        # 6. Internal migration % (born outside current province, OS_01_00033_01)
        best_mig: dict[str, int] = {}
        with open(self.raw_dir / "migration.csv", encoding="utf-8-sig", errors="replace") as f:
            for row in csv.DictReader(f):
                yr = _be_to_ce(row.get("year"))
                val = _to_float(row.get("value"))
                if not yr or val is None:
                    continue
                pr = (row.get("province") or "").strip()
                if pr in ("รวม", "ทั่วประเทศ", "ทั่วราชอาณาจักร"):
                    if yr >= best_mig.get("NAT", 0):
                        best_mig["NAT"] = yr
                        national["born_outside_province"] = round(val / 100.0, 4)
                    continue
                code = resolve_province(pr)
                if code and yr >= best_mig.get(code, 0):
                    best_mig[code] = yr
                    _rec(code)["born_outside_province"] = round(val / 100.0, 4)

        # 7. Business & Industrial Census establishments (SFD_SPB1201)
        best_est: dict[str, int] = {}
        with open(self.raw_dir / "establishments.csv", encoding="utf-8-sig", errors="replace") as f:
            for row in csv.DictReader(f):
                yr = _be_to_ce(row.get("year"))
                val = _to_float(row.get("value"))
                if not yr or val is None:
                    continue
                var = (row.get("variable") or "").strip()
                a1 = (row.get("size_est_eco_act1") or "").strip()
                a2 = (row.get("size_est_eco_act2") or "").strip()
                if "สถานประกอบการ" in var and "ขนาดของสถานประกอบการ" in a1 and a2 == "รวม":
                    code = resolve_province(row.get("province"))
                    if code and yr >= best_est.get(code, 0):
                        best_est[code] = yr
                        _rec(code)["establishments"] = round(val)

        return {
            "vintage": f"NSO SES {max(years.values(), default=2025)} & Business Census",
            "years": years,
            "national": national,
            "provinces": provinces,
            "_files": [f"{k}.csv" for k in TABLES],
        }
