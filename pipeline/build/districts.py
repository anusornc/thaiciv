"""Build districts.json: real industry specialization Districts & City-Type Badges from NESDC 2024p 19-sector GPP."""

from __future__ import annotations

import json

from ..core.paths import WEB_DATA
from ..core.store import load_interim, save_web
from .yields import INDUSTRIES

REQUIRES = ["_world", "nesdc_gpp", "cities.json"]
PRODUCES = ["districts.json"]

CATALOG = [
    {
        "id": "campus",
        "name": "Campus",
        "icon": "d-campus",
        "color": "#4a7bd0",
        "naics": ["education", "professional", "information"],
        "own": [],
        "sub": {"education": "Universities & schools", "professional": "Scientific & technical", "information": "Digital & telecom"},
        "badge": {"id": "scientific", "label": "Knowledge city", "labels": {"information": "Tech hub", "professional": "Research city", "education": "University city"}},
        "description": "Education, information & communications, and professional/scientific/technical value added (NESDC GPP).",
        "caveat": None,
    },
    {
        "id": "commercial_hub",
        "name": "Commercial hub",
        "icon": "d-commercial_hub",
        "color": "#d4a83b",
        "naics": ["finance", "trade", "real_estate"],
        "own": [],
        "sub": {"finance": "Banking & finance", "trade": "Wholesale & retail", "real_estate": "Real estate"},
        "badge": {"id": "commercial", "label": "Trade hub", "labels": {"finance": "Finance city", "trade": "Commerce hub"}},
        "description": "Financial & insurance activities, wholesale/retail trade, and real estate (NESDC GPP).",
        "caveat": None,
    },
    {
        "id": "industrial_zone",
        "name": "Industrial zone",
        "icon": "d-industrial_zone",
        "color": "#d97b36",
        "naics": ["manufacturing", "mining"],
        "own": [],
        "sub": {"manufacturing": "Manufacturing & EEC factories", "mining": "Mining & gas extraction"},
        "badge": {"id": "industrial", "label": "Industrial hub", "labels": {"manufacturing": "Factory powerhouse", "mining": "Mining & energy hub"}},
        "description": "Manufacturing and mining & quarrying value added (NESDC GPP — Rayong, Chon Buri, Ayutthaya, Lamphun, Samut Prakan).",
        "caveat": None,
    },
    {
        "id": "entertainment_complex",
        "name": "Entertainment complex",
        "icon": "d-entertainment_complex",
        "color": "#c95ca8",
        "naics": ["accommodation", "arts"],
        "own": [],
        "sub": {"accommodation": "Hotels, resorts & dining", "arts": "Arts & recreation"},
        "badge": {"id": "entertainment", "label": "Resort city", "labels": {"accommodation": "Resort & tourism city", "arts": "Culture & leisure city"}},
        "description": "Accommodation, food services, arts & recreation value added (NESDC GPP — Phuket, Krabi, Phang Nga, Surat Thani).",
        "caveat": None,
    },
    {
        "id": "harbor",
        "name": "Harbor",
        "icon": "d-harbor",
        "color": "#3c99b8",
        "naics": ["transportation"],
        "own": [],
        "sub": {"transportation": "Ports, shipping & logistics"},
        "badge": {"id": "maritime", "label": "Port & logistics hub", "labels": {"transportation": "Logistics & port city"}},
        "description": "Transportation and storage value added in coastal or Chao Phraya corridor provinces (NESDC GPP).",
        "caveat": None,
    },
    {
        "id": "government_plaza",
        "name": "Government plaza",
        "icon": "d-government_plaza",
        "color": "#8c6ec9",
        "naics": ["public_admin", "health"],
        "own": [],
        "sub": {"public_admin": "Public administration & defence", "health": "Public health & hospitals"},
        "badge": {"id": "governmental", "label": "Regional capital", "labels": {"public_admin": "Administrative hub", "health": "Medical hub"}},
        "description": "Public administration, defence, and human health value added (NESDC GPP).",
        "caveat": None,
    },
    {
        "id": "aqueduct",
        "name": "Aqueduct & dam",
        "icon": "d-aqueduct",
        "color": "#4ca372",
        "naics": ["utilities", "water_waste", "construction"],
        "own": [],
        "sub": {"utilities": "Power generation & grid", "water_waste": "Water & utilities", "construction": "Construction"},
        "badge": {"id": "utility", "label": "Power & utility hub", "labels": {"utilities": "Energy hub"}},
        "description": "Electricity, gas, water supply and construction value added (NESDC GPP — Lampang, Ratchaburi, Kanchanaburi).",
        "caveat": None,
    },
    {
        "id": "theater_square",
        "name": "Granary & farmstead",
        "icon": "d-theater_square",
        "color": "#7eb844",
        "naics": ["agriculture"],
        "own": [],
        "sub": {"agriculture": "Rice, rubber, fruit & fisheries"},
        "badge": {"id": "cultural", "label": "Agricultural hub", "labels": {"agriculture": "Farm & rice bowl"}},
        "description": "Agriculture, forestry and fishing specialization (NESDC GPP — Isan rice bowl, Southern rubber/palm & Northern orchards).",
        "caveat": None,
    },
]


def build() -> None:
    w = load_interim("_world")
    gpp = load_interim("nesdc_gpp")
    cities = json.loads((WEB_DATA / "cities.json").read_text(encoding="utf-8"))

    water = w["water"]
    from ..core.hexgrid import HexGrid
    grid = HexGrid(**w["grid"])

    nat_sec = (gpp.get("national") or {}).get("sectors_thb") or {}
    nat_tot = sum(nat_sec.values()) or 1.0

    # Precompute national share for each district & sector
    nat_dist_share = {
        d["id"]: sum(nat_sec.get(s, 0.0) for s in d["naics"]) / nat_tot for d in CATALOG
    }
    nat_sec_share = {k: v / nat_tot for k, v in nat_sec.items()}

    # Check coastal/water adjacency for Harbor
    def has_water(footprint: list[int]) -> bool:
        for c in footprint:
            if water[c] > 0:
                return True
            for nb in grid.neighbours(c):
                if water[nb] > 0:
                    return True
        return False

    cities_out: dict[str, dict | None] = {}
    counties_out: dict[str, dict] = {}

    for c in cities:
        code = c["id"]
        g = gpp["provinces"].get(code)
        if not g or not g.get("sectors_thb"):
            cities_out[code] = None
            continue
        sec = g["sectors_thb"]
        tot = sum(sec.values()) or 1.0
        coastal = has_water(c["footprint"])

        # Top industries by LQ
        top = []
        for sk, sv in sec.items():
            if not sv or sv <= 0:
                continue
            ns = nat_sec_share.get(sk, 0.0)
            if ns <= 0:
                continue
            lq = (sv / tot) / ns
            top.append({
                "naics": sk,
                "emp": round(sv / 1e6, 1),  # Million THB value added
                "lq": round(lq, 2),
                "avg_pay": None,
                "oty_pct": None,
                "suppressed": 0,
                "lower_bound": False,
            })
        top.sort(key=lambda x: -x["lq"])
        top = top[:8]

        # Score every district
        passing = []
        for d in CATALOG:
            if d["id"] == "harbor" and not coastal and code != "10":
                continue
            val = sum(sec.get(s, 0.0) for s in d["naics"])
            share = val / tot
            ns = nat_dist_share[d["id"]]
            lq = (share / ns) if ns > 0 else 0.0

            # Best sub-sector
            best_sub, best_sub_lq, best_sub_val = None, 0.0, 0.0
            for sk in d["naics"]:
                sv = sec.get(sk, 0.0)
                sns = nat_sec_share.get(sk, 0.0)
                if sv > 0 and sns > 0:
                    slq = (sv / tot) / sns
                    if slq > best_sub_lq and (sv / tot) >= 0.02:
                        best_sub, best_sub_lq, best_sub_val = sk, slq, sv

            broad_ok = lq >= 1.15 and share >= 0.03
            spec_ok = best_sub is not None and best_sub_lq >= 1.8 and (best_sub_val / tot) >= 0.03
            if not (broad_ok or spec_ok):
                continue

            strength = max(val - val / max(1.01, lq), best_sub_val - best_sub_val / max(1.01, best_sub_lq))
            passing.append({
                "id": d["id"],
                "lq": round(lq, 2),
                "emp": round(val / 1e6, 1),
                "share": round(share, 4),
                "avg_pay": None,
                "sub": best_sub if best_sub_lq > 1.1 else None,
                "sub_lq": round(best_sub_lq, 2) if best_sub and best_sub_lq > 1.1 else None,
                "sub_emp": round(best_sub_val / 1e6, 1) if best_sub and best_sub_lq > 1.1 else None,
                "sub_lower_bound": False,
                "via": "broad" if broad_ok else "specialty",
                "strength": round(strength / 1e6, 1),
                "suppressed": 0,
                "lower_bound": False,
            })

        passing.sort(key=lambda x: -x["strength"])
        passing = passing[:5]

        # City-type badge
        badge = None
        if c.get("capital"):
            badge = {
                "id": "governmental",
                "label": "Capital city",
                "district": "government_plaza",
                "basis": "nesdc",
                "text": "National capital & financial centre (33% of Thailand's GDP)",
            }
        elif passing:
            # Prefer a standout extreme specialization (LQ >= 2.2 & share >= 8%), else top strength
            standout = [p for p in passing if p["lq"] >= 2.2 and p["share"] >= 0.08]
            chosen = standout[0] if standout else passing[0]
            cat = next(x for x in CATALOG if x["id"] == chosen["id"])
            lbl = cat["badge"]["label"]
            if chosen.get("sub") and (chosen.get("sub_lq") or 0) >= 1.6:
                lbl = cat["badge"]["labels"].get(chosen["sub"], lbl)
            sub_name = cat["sub"].get(chosen.get("sub"), cat["name"]) if chosen.get("sub") else cat["name"]
            lq_show = chosen["sub_lq"] if (chosen.get("sub") and (chosen.get("sub_lq") or 0) > chosen["lq"]) else chosen["lq"]
            badge = {
                "id": cat["badge"]["id"],
                "label": lbl,
                "district": chosen["id"],
                "basis": "nesdc",
                "text": f"{sub_name}: {lq_show:.1f}× the national share of GPP",
            }

        cities_out[code] = {
            "emp": round(tot / 1e6, 1),
            "avg_pay": c.get("monthly_income"),
            "counties": [len(c["counties"]), len(c["counties"])],
            "top": top,
            "districts": passing,
            "badge": badge,
        }

        for geoid in c["counties"]:
            counties_out[geoid] = {
                "emp": round(tot / 1e6, 1),
                "districts": [[p["id"], p["lq"], p["emp"]] for p in passing[:3]],
            }

    save_web(
        "districts.json",
        {
            "version": 1,
            "vintage": gpp.get("vintage", "NESDC GPP 2024p"),
            "year": gpp["year"],
            "sources": ["nesdc_gpp"],
            "rule": {
                "min_lq": 1.15,
                "min_jobs": 1,
                "min_share": 0.03,
                "specialty_lq": 1.8,
                "specialty_jobs": 1,
                "specialty_share": 0.03,
                "max_per_city": 5,
                "harbor_needs_water": True,
                "badge_lq": 2.2,
                "badge_share": 0.08,
                "text": "A district appears when its sector Location Quotient (LQ) ≥ 1.15 and share ≥ 3% of provincial GPP (NESDC 2024p), or when a speciality has LQ ≥ 1.8. Ranked by output above the national norm.",
                "county_note": "Provincial NESDC 2024p GPP specialization mapped to each province's districts.",
            },
            "catalog": CATALOG,
            "industries": {k: {"title": v, "us_emp": round(nat_sec.get(k, 0.0) / 1e6, 1)} for k, v in INDUSTRIES.items()},
            "national": {"emp": round(nat_tot / 1e6, 1), "avg_pay": None},
            "cities": cities_out,
            "counties": counties_out,
        },
    )
