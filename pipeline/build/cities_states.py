"""Build cities.json, states.json, and nation.json for Thailand's 77 provinces and urban hubs."""

from __future__ import annotations

import math

from ..core.geo import MapProjection
from ..core.hexgrid import HexGrid
from ..core.store import load_interim, save_web
from ..core.thailand import BY_CODE, short_city_name
from .yields import INDUSTRIES, YIELD_DEFS, compute_yields, rank_map

REQUIRES = ["_world", "thailand_boundaries", "nesdc_gpp", "dopa_population", "nso_ses", "nso_labor", "resources.json"]
PRODUCES = ["cities.json", "states.json", "nation.json"]


def _nearest_land_cell(grid: HexGrid, owner: list[int], x: float, y: float, want_owner: int, used: set[int]) -> int:
    """Find best land cell for a city banner: prefer own province & unused cell."""
    c0 = grid.cell_at(x, y)
    if c0 >= 0 and owner[c0] == want_owner and c0 not in used:
        return c0
    # Search all cells owned by this province, nearest to (x, y)
    own_cells = [i for i, o in enumerate(owner) if o == want_owner]
    own_cells.sort(key=lambda i: (grid.cx(i) - x) ** 2 + (grid.cy(i) - y) ** 2)
    for i in own_cells:
        if i not in used:
            return i
    if own_cells:
        return own_cells[0]
    # Fallback: any Thailand land cell nearest (x, y)
    land = [i for i, o in enumerate(owner) if o >= 0]
    return min(land, key=lambda i: (grid.cx(i) - x) ** 2 + (grid.cy(i) - y) ** 2)


def _compute_growth(series: dict[str, int] | None) -> tuple[float | None, list[int] | None]:
    if not series:
        return None, None
    if "2021" in series and "2025" in series and series["2021"] > 0:
        g = series["2025"] / series["2021"] - 1.0
        if abs(g) <= 0.35:
            return round(g, 4), [2021, 2025]
    return None, None


def build() -> None:
    w = load_interim("_world")
    tb = load_interim("thailand_boundaries")
    gpp = load_interim("nesdc_gpp")
    dopa = load_interim("dopa_population")
    ses = load_interim("nso_ses")
    lfs = load_interim("nso_labor")

    from ..core.paths import WEB_DATA
    import json
    res_path = WEB_DATA / "resources.json"
    resources = json.loads(res_path.read_text(encoding="utf-8")) if res_path.exists() else None

    grid = HexGrid(**w["grid"])
    proj = MapProjection(**w["projection"])
    owner = w["owner"]
    cover = w["cover"]
    pct = w["pct"]

    provinces = tb["provinces"]
    prov_index = {p["fips"]: i for i, p in enumerate(provinces)}
    districts_by_prov: dict[str, list[str]] = {}
    for d in tb["districts"]:
        districts_by_prov.setdefault(d["state_fips"], []).append(d["geoid"])

    # Precompute cells per province
    cells_by_prov: dict[int, list[int]] = {i: [] for i in range(len(provinces))}
    for i, o in enumerate(owner):
        if o >= 0:
            cells_by_prov[o].append(i)

    # Precompute land shares & mapped energy MW per province
    mw_types = [t["id"] for t in (resources or {}).get("types", []) if t.get("unit") == "MW"]
    energy_by_abbr: dict[str, dict] = {}
    if resources and mw_types:
        for p in provinces:
            energy_by_abbr[p["abbr"]] = {
                "unit": "MW",
                "total": 0.0,
                "by_type": {t: 0.0 for t in mw_types},
                "sites": {t: 0 for t in mw_types},
                "note": "Sum of mapped power plant sites in resources.json (WRI Global Power Plant Database).",
            }
        for it in resources.get("items", []):
            st_abbr = it.get("state")
            t = it.get("type")
            v = it.get("value")
            if st_abbr in energy_by_abbr and t in energy_by_abbr[st_abbr]["by_type"] and v is not None:
                energy_by_abbr[st_abbr]["by_type"][t] = round(energy_by_abbr[st_abbr]["by_type"][t] + v, 1)
                energy_by_abbr[st_abbr]["sites"][t] += 1
                energy_by_abbr[st_abbr]["total"] = round(energy_by_abbr[st_abbr]["total"] + v, 1)

    # Assemble province & city records
    states_out: list[dict] = []
    cities_out: list[dict] = []
    used_cells: set[int] = set()

    # Sort placement priority by population descending so Bangkok & major hubs always get their exact center hex
    pop_order = sorted(
        provinces,
        key=lambda p: -(dopa["provinces"].get(p["fips"], {}).get("population") or 0),
    )
    banner_cell_by_fips: dict[str, int] = {}
    for p in pop_order:
        pi = prov_index[p["fips"]]
        x, y = proj(p["cap_lon"], p["cap_lat"])
        c = _nearest_land_cell(grid, owner, x, y, pi, used_cells)
        used_cells.add(c)
        banner_cell_by_fips[p["fips"]] = c

    nat_pop_series: dict[str, int] = {}
    nat_employed = 0
    nat_unemployed = 0

    for pi, p in enumerate(provinces):
        code = p["fips"]
        abbr = p["abbr"]
        g = gpp["provinces"].get(code) or {}
        dp = dopa["provinces"].get(code) or {}
        se = ses["provinces"].get(code) or {}
        lf = lfs["provinces"].get(code) or {}

        pop = dp.get("population") or g.get("nesdc_pop") or 0
        pseries = dp.get("series") or None
        if pseries:
            for yr, val in pseries.items():
                nat_pop_series[yr] = nat_pop_series.get(yr, 0) + val
        growth, growth_years = _compute_growth(pseries)

        emp = lf.get("employed")
        unemp_cnt = lf.get("unemployed") or 0
        if emp:
            nat_employed += emp
            nat_unemployed += unemp_cnt
        unemp_rate = lf.get("unemployment_rate")

        sectors = g.get("sectors_thb") or {}
        gpp_thb = g.get("gpp_thb")
        yields = compute_yields(gpp_thb, sectors)

        # Annualize monthly household income & expenditure to match Civ panel expectations cleanly
        m_inc = se.get("monthly_income_thb")
        m_exp = se.get("monthly_expense_thb")
        debt = se.get("household_debt_thb")
        exp_ratio = se.get("expense_to_income_pct")
        rent_burden = round(exp_ratio / 100.0, 4) if exp_ratio is not None else (
            round(m_exp / m_inc, 4) if (m_inc and m_exp and m_inc > 0) else None
        )

        # Land cover averages over province cells
        pcells = cells_by_prov[pi]
        cov_cells = [i for i in pcells if cover[i] > 0]
        land = None
        if cov_cells:
            land = {
                k: round(sum(pct[k][i] for i in cov_cells) / (100.0 * len(cov_cells)), 3)
                for k in pct
            }

        # Sector breakdown (in Million THB) used for industry bars & specialization LQs
        jobs_mthb = {k: round(v / 1e6, 1) for k, v in sectors.items() if v and v > 0}

        econ_common = {
            "population": pop,
            "employed": emp,
            "yields": yields,
            "jobs": jobs_mthb,
            "median_income": round(m_inc * 12) if m_inc is not None else None,  # Annual household income (THB)
            "monthly_income": round(m_inc) if m_inc is not None else None,
            "median_rent": round(m_exp) if m_exp is not None else None,         # Monthly household expenditure (THB)
            "home_value": round(debt) if debt is not None else None,            # Average household debt (THB)
            "unemployment": unemp_rate,
            "rent_burden": rent_burden,
            "gdp": gpp_thb,
            "gdp_year": gpp["year"],
            "gdp_by_industry": sectors,
            "growth": growth,
            "growth_years": growth_years,
        }

        states_out.append({
            "fips": code,
            "abbr": abbr,
            "name": p["name"],
            "th_name": p["th_name"],
            "region": p["region"],
            **econ_common,
            "ranks": {},
            "land": land,
            "energy": energy_by_abbr.get(abbr),
        })

        x, y = proj(p["cap_lon"], p["cap_lat"])
        cell = banner_cell_by_fips[code]
        footprint = sorted(set(pcells + [cell]))
        cities_out.append({
            "id": code,
            "name": short_city_name(code),
            "full": f"{p['name']} ({p['th_name']}) · {p['region']} Region",
            "th_name": p["th_name"],
            "region": p["region"],
            "states": [abbr],
            "metro": True,
            "capital": code == "10",
            "x": round(x, 1),
            "y": round(y, 1),
            "cell": cell,
            **econ_common,
            "counties": sorted(districts_by_prov.get(code, [])),
            "footprint": footprint,
            "pop_series": pseries,
            "ranks": {},
            "peers": [],
        })

    # Compute state ranks
    for yk in ("food", "production", "gold", "science", "culture"):
        rm = rank_map(
            [{"id": s["fips"], "population": s["population"], "v": s["yields"].get(yk)} for s in states_out],
            lambda r: r["v"],
        )
        for s in states_out:
            s["ranks"][yk] = rm[s["fips"]]

    # Sort cities by population descending, compute ranks & 5 closest peers
    cities_out.sort(key=lambda c: -(c["population"] or 0))
    rank_fns = {
        "population": lambda c: c["population"],
        "gdp": lambda c: c["gdp"],
        "gdp_per_capita": lambda c: (c["gdp"] / c["population"]) if (c["gdp"] and c["population"]) else None,
        "growth": lambda c: c["growth"],
        "food": lambda c: c["yields"].get("food"),
        "production": lambda c: c["yields"].get("production"),
        "gold": lambda c: c["yields"].get("gold"),
        "science": lambda c: c["yields"].get("science"),
        "culture": lambda c: c["yields"].get("culture"),
    }
    all_ranks = {k: rank_map(cities_out, fn) for k, fn in rank_fns.items()}
    for c in cities_out:
        c["ranks"] = {k: all_ranks[k][c["id"]] for k in rank_fns}
        lp = math.log(max(1, c["population"] or 1))
        peers = sorted(
            (o for o in cities_out if o["id"] != c["id"] and (o["population"] or 0) > 0),
            key=lambda o: abs(math.log(o["population"]) - lp),
        )
        c["peers"] = [o["id"] for o in peers[:5]]

    # National summary (Whole Kingdom)
    nat_gpp = gpp["national"] or {}
    nat_sectors = nat_gpp.get("sectors_thb") or {}
    nat_gpp_thb = nat_gpp.get("gpp_thb") or sum((s["gdp"] or 0) for s in states_out)
    nat_pop = nat_pop_series.get("2025") or sum((s["population"] or 0) for s in states_out)
    nat_growth, nat_gyrs = _compute_growth(nat_pop_series)
    nat_ses = ses.get("national") or {}
    nat_m_inc = nat_ses.get("monthly_income_thb") or (
        sum((s["monthly_income"] or 0) * (s["population"] or 0) for s in states_out) / max(1, nat_pop)
    )
    nat_m_exp = nat_ses.get("monthly_expense_thb") or (
        sum((s["median_rent"] or 0) * (s["population"] or 0) for s in states_out) / max(1, nat_pop)
    )
    nat_debt = nat_ses.get("household_debt_thb") or (
        sum((s["home_value"] or 0) * (s["population"] or 0) for s in states_out) / max(1, nat_pop)
    )
    nat_unemp = round(nat_unemployed / (nat_employed + nat_unemployed), 4) if (nat_employed + nat_unemployed) > 0 else None

    nation_out = {
        "vintage": "DOPA 2025 · NSO SES & LFS",
        "year": 2025,
        "gdp_vintage": gpp.get("vintage", "NESDC GPP 2024p"),
        "currency": "THB",
        "nation": {
            "population": nat_pop,
            "employed": nat_employed,
            "yields": compute_yields(nat_gpp_thb, nat_sectors),
            "jobs": {k: round(v / 1e6, 1) for k, v in nat_sectors.items() if v and v > 0},
            "median_income": round(nat_m_inc * 12) if nat_m_inc else None,
            "monthly_income": round(nat_m_inc) if nat_m_inc else None,
            "median_rent": round(nat_m_exp) if nat_m_exp else None,
            "home_value": round(nat_debt) if nat_debt else None,
            "unemployment": nat_unemp,
            "rent_burden": round(nat_m_exp / nat_m_inc, 4) if (nat_m_inc and nat_m_exp) else None,
            "gdp": nat_gpp_thb,
            "gdp_year": gpp["year"],
            "gdp_by_industry": nat_sectors,
            "growth": nat_growth,
            "growth_years": nat_gyrs,
        },
        "yields": YIELD_DEFS,
        "industries": INDUSTRIES,
    }

    save_web("states.json", states_out)
    save_web("cities.json", cities_out)
    save_web("nation.json", nation_out)
