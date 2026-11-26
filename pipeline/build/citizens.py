"""Build citizens.json: per-province citizen figure rows (workforce sectors, residency & citizenship) for City View."""

from __future__ import annotations

import json

from ..core.paths import WEB_DATA
from ..core.store import load_interim, save_web

REQUIRES = ["nesdc_gpp", "dopa_population", "nso_ses", "cities.json"]
PRODUCES = ["citizens.json"]

WORKFORCE_GROUPS = [
    {"key": "farmer", "label": "Agriculture & fishing", "icon": "c-farmer", "sectors": ["agriculture"]},
    {"key": "maker", "label": "Manufacturing & mining", "icon": "c-maker", "sectors": ["manufacturing", "mining"]},
    {"key": "builder", "label": "Construction & utilities", "icon": "c-builder", "sectors": ["construction", "utilities", "water_waste"]},
    {"key": "clerk", "label": "Trade & logistics", "icon": "c-clerk", "sectors": ["trade", "transportation"]},
    {"key": "service", "label": "Hospitality, tourism & arts", "icon": "c-service", "sectors": ["accommodation", "arts", "other"]},
    {"key": "executive", "label": "Finance, real estate & admin", "icon": "c-executive", "sectors": ["finance", "real_estate", "admin"]},
    {"key": "engineer", "label": "Tech & scientific", "icon": "c-engineer", "sectors": ["information", "professional"]},
    {"key": "scholar", "label": "Education & public admin", "icon": "c-scholar", "sectors": ["education", "public_admin"]},
    {"key": "healer", "label": "Health & social work", "icon": "c-healer", "sectors": ["health"]},
]

NATIVITY_GROUPS = [
    {"key": "born_in_state", "label": "Thai · born in province", "icon": "c-born_in_state", "lines": "DOPA + NSO"},
    {"key": "other_state", "label": "Thai · internal migrant", "icon": "c-other_state", "lines": "NSO OS_01_00033_01"},
    {"key": "foreign_born", "label": "Non-Thai registered", "icon": "c-foreign_born", "lines": "DOPA 2025"},
]


def _largest_remainder(shares: dict[str, float], total_figs: int) -> dict[str, int]:
    raw = {k: v * total_figs for k, v in shares.items()}
    floored = {k: int(v) for k, v in raw.items()}
    rem = total_figs - sum(floored.values())
    order = sorted(shares, key=lambda k: -(raw[k] - floored[k]))
    for k in order[:max(0, rem)]:
        floored[k] += 1
    return floored


def _make_workforce_row(sec: dict[str, float], emp_total: int | None) -> dict | None:
    tot_val = sum(sec.values())
    if tot_val <= 0:
        return None
    base = emp_total or round(tot_val / 1e6)
    shares = {}
    counts = {}
    for g in WORKFORCE_GROUPS:
        sv = sum(sec.get(s, 0.0) for s in g["sectors"])
        sh = sv / tot_val
        shares[g["key"]] = round(sh, 3)
        counts[g["key"]] = round(sh * base)
    return {
        "total": base,
        "counts": counts,
        "shares": shares,
        "figures": _largest_remainder({k: sum(sec.get(s, 0.0) for s in g["sectors"]) / tot_val for g in WORKFORCE_GROUPS for k in [g["key"]]}, 20),
    }


def _make_nativity_row(pop: int, non_thai: int, mig_rate: float | None) -> dict | None:
    if not pop or pop <= 0:
        return None
    f_sh = min(0.95, max(0.0, non_thai / pop))
    thai_sh = 1.0 - f_sh
    m_sh = min(thai_sh, max(0.0, mig_rate or 0.0))
    loc_sh = max(0.0, thai_sh - m_sh)
    shares = {
        "born_in_state": round(loc_sh, 3),
        "other_state": round(m_sh, 3),
        "foreign_born": round(f_sh, 3),
    }
    counts = {k: round(v * pop) for k, v in shares.items()}
    return {
        "total": pop,
        "counts": counts,
        "shares": shares,
        "figures": _largest_remainder({"born_in_state": loc_sh, "other_state": m_sh, "foreign_born": f_sh}, 10),
        "foreign_born": round(f_sh, 3),
        "born_in_state": round(loc_sh, 3),
    }


def build() -> None:
    gpp = load_interim("nesdc_gpp")
    dopa = load_interim("dopa_population")
    ses = load_interim("nso_ses")
    cities = json.loads((WEB_DATA / "cities.json").read_text(encoding="utf-8"))

    nat_sec = (gpp.get("national") or {}).get("sectors_thb") or {}
    nat_pop = sum((d.get("population") or 0) for d in dopa["provinces"].values())
    nat_non_thai = sum((d.get("non_thai") or 0) for d in dopa["provinces"].values())
    nat_mig = (ses.get("national") or {}).get("born_outside_province") or 0.14
    nat_emp = sum((c.get("employed") or 0) for c in cities)

    nat_wf = _make_workforce_row(nat_sec, nat_emp)
    nat_nat = _make_nativity_row(nat_pop, nat_non_thai, nat_mig)

    national_row = {
        "workforce": nat_wf,
        "age": None,
        "commute": None,
        "education": None,
        "nativity": nat_nat,
        "specialists": [],
    }

    cities_out: dict[str, dict | None] = {}
    for c in cities:
        code = c["id"]
        g = gpp["provinces"].get(code) or {}
        dp = dopa["provinces"].get(code) or {}
        se = ses["provinces"].get(code) or {}

        wf = _make_workforce_row(g.get("sectors_thb") or {}, c.get("employed"))
        nat = _make_nativity_row(dp.get("population") or 0, dp.get("non_thai") or 0, se.get("born_outside_province"))

        # Specialists vs Thailand national norm
        hi, lo = [], []
        for rname, row, nrow in (("workforce", wf, nat_wf), ("nativity", nat, nat_nat)):
            if not row or not nrow:
                continue
            for k, sh in row["shares"].items():
                nsh = nrow["shares"].get(k, 0.0)
                if sh < 0.01 and nsh < 0.01:
                    continue
                if nsh <= 0:
                    continue
                rat = sh / nsh
                if rat >= 1.5:
                    hi.append({"row": rname, "key": k, "share": sh, "national": nsh, "ratio": round(rat, 2)})
                elif rat <= 0.67:
                    lo.append({"row": rname, "key": k, "share": sh, "national": nsh, "ratio": round(rat, 2)})
        hi.sort(key=lambda x: -x["ratio"])
        lo.sort(key=lambda x: x["ratio"])

        cities_out[code] = {
            "workforce": wf,
            "age": None,
            "commute": None,
            "education": None,
            "nativity": nat,
            "specialists": hi[:4] + lo[:2],
            "reliable": True,
        }

    save_web(
        "citizens.json",
        {
            "version": 1,
            "vintage": "NESDC GPP 2024p · DOPA 2025 · NSO",
            "year": 2025,
            "sources": ["nesdc_gpp", "dopa_population", "nso_ses"],
            "figures": {"workforce": 20, "nativity": 10},
            "rows": {
                "workforce": "Economic activity mix (NESDC 2024p GPP shares × 20 figures)",
                "nativity": "Residency & citizenship mix (DOPA 2025 + NSO migration × 10 figures)",
            },
            "groups": {
                "workforce": [{"key": g["key"], "label": g["label"], "icon": g["icon"], "lines": ", ".join(g["sectors"])} for g in WORKFORCE_GROUPS],
                "age": [],
                "commute": [],
                "education": [],
                "nativity": NATIVITY_GROUPS,
            },
            "rule": {
                "specialist_high": 1.5,
                "specialist_low": 0.67,
                "min_share": 0.01,
                "max_high": 4,
                "max_low": 2,
                "text": "Categories at ≥1.5× or ≤0.67× Thailand's national share are flagged as specialists.",
            },
            "national": national_row,
            "cities": cities_out,
        },
    )
