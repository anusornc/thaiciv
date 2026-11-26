"""Build military.json: Royal Thai Armed Forces installations (RTAF, RTN, RTA) from public records & Wikidata."""

from __future__ import annotations

from ..core.geo import MapProjection
from ..core.hexgrid import HexGrid
from ..core.store import load_interim, save_web
from ..core.thailand import BY_CODE

REQUIRES = ["_world", "wikidata_thailand"]
PRODUCES = ["military.json"]

# Major publicly documented Royal Thai Armed Forces headquarters, air wings & naval bases
# (Headcounts are not published by province by Thailand MoD and stay null — never invented.)
INSTALLATIONS = [
    ("rtn-sattahip", "Sattahip Naval Base (Royal Thai Fleet HQ)", "navy", "major", 100.9030, 12.6600),
    ("rtn-utapao", "U-Tapao Royal Thai Navy Airfield", "navy", "major", 101.0050, 12.6799),
    ("rtaf-donmueang", "Don Mueang RTAF Base (RTAF HQ)", "air_force", "major", 100.6067, 13.9126),
    ("rtaf-wing1", "Korat RTAF Base (Wing 1)", "air_force", "major", 102.0786, 14.9345),
    ("rtaf-wing2", "Khok Kathiam RTAF Base (Wing 2, Lop Buri)", "air_force", "base", 100.6633, 14.8744),
    ("rtaf-wing4", "Takhli RTAF Base (Wing 4, Nakhon Sawan)", "air_force", "major", 100.2958, 15.2773),
    ("rtaf-wing7", "Surat Thani RTAF Base (Wing 7)", "air_force", "major", 99.1356, 9.1326),
    ("rtaf-wing21", "Ubon Ratchathani RTAF Base (Wing 21)", "air_force", "base", 104.8703, 15.2513),
    ("rtaf-wing23", "Udon Thani RTAF Base (Wing 23)", "air_force", "base", 102.7883, 17.3864),
    ("rtaf-wing41", "Chiang Mai RTAF Base (Wing 41)", "air_force", "base", 98.9628, 18.7668),
    ("rtaf-wing46", "Phitsanulok RTAF Base (Wing 46)", "air_force", "base", 100.2791, 16.7829),
    ("rtaf-wing56", "Hat Yai RTAF Base (Wing 56, Songkhla)", "air_force", "base", 100.3929, 6.9332),
    ("rtn-phangnga", "Phang Nga Naval Base (3rd Naval Area)", "navy", "base", 98.2290, 8.5750),
    ("rtn-songkhla", "Songkhla Naval Base (2nd Naval Area)", "navy", "base", 100.5940, 7.2110),
    ("rta-1st-army", "1st Army Area HQ (Bangkok)", "army", "major", 100.5110, 13.7670),
    ("rta-2nd-army", "Fort Suranaree (2nd Army Area HQ, Korat)", "army", "major", 102.0940, 14.9590),
    ("rta-3rd-army", "Fort Somdet Phra Naresuan (3rd Army HQ, Phitsanulok)", "army", "major", 100.2660, 16.8260),
    ("rta-4th-army", "Fort Wachirawut (4th Army HQ, Nakhon Si Thammarat)", "army", "major", 99.9610, 8.4810),
    ("rta-lopburi", "Special Warfare Command (Lop Buri)", "army", "major", 100.6550, 14.8050),
    ("rta-prachin", "Fort Chakrabongse (2nd Infantry Div., Prachin Buri)", "army", "base", 101.3660, 14.0630),
    ("rta-kanchanaburi", "Fort Surasi (9th Infantry Div., Kanchanaburi)", "army", "base", 99.4520, 14.1220),
]


def build() -> None:
    w = load_interim("_world")
    grid = HexGrid(**w["grid"])
    proj = MapProjection(**w["projection"])
    owner = w["owner"]
    county_arr = w["county"]
    states_fips = w["states"]
    counties_geoid = w["counties"]

    inst_out = []
    cities_mil: dict[str, dict] = {}
    for iid, name, comp, tier, lon, lat in INSTALLATIONS:
        x, y = proj(lon, lat)
        c = grid.cell_at(x, y)
        if c < 0 or owner[c] < 0:
            land = [i for i, o in enumerate(owner) if o >= 0]
            c = min(land, key=lambda i: (grid.cx(i) - x) ** 2 + (grid.cy(i) - y) ** 2)
        pcode = states_fips[owner[c]]
        abbr = BY_CODE[pcode][1]
        ci = county_arr[c]
        inst_out.append({
            "id": iid,
            "name": name,
            "component": comp,
            "joint": False,
            "status": "act",
            "tier": tier,
            "curated": True,
            "area_km2": None,
            "cells": None,
            "x": round(x, 1),
            "y": round(y, 1),
            "cell": c,
            "county": counties_geoid[ci] if ci >= 0 else None,
            "cbsa": pcode,
            "state": abbr,
            "state_filed": abbr,
        })
        cm = cities_mil.setdefault(pcode, {"tier": "garrison", "armed_forces": None, "share": None, "naval": False, "installations": [], "installation_count": 0})
        cm["installations"].append(iid)
        cm["installation_count"] += 1
        if tier == "major" and cm["installation_count"] >= 2:
            cm["tier"] = "fortress"
        if comp == "navy":
            cm["naval"] = True

    save_web(
        "military.json",
        {
            "version": 1,
            "vintage": {"installations": "Public Royal Thai Armed Forces directory & Wikidata (2026)"},
            "sources": ["wikidata_thailand"],
            "rule": "Publicly documented Royal Thai Army regional commands, Royal Thai Navy fleet bases and Royal Thai Air Force active wings.",
            "rules": {
                "installations": "Major active Royal Thai Army, Navy and Air Force bases from public records and Wikidata.",
                "encampment": "Provinces hosting a major regional command, naval fleet base or active air wing.",
            },
            "flagships": ["Sattahip Naval Base (Royal Thai Fleet HQ)", "Don Mueang RTAF Base (RTAF HQ)", "Fort Suranaree (2nd Army Area HQ, Korat)"],
            "caveats": "Personnel headcounts and defense outlays by province are not published by Thailand's Ministry of Defence and are intentionally left null rather than estimated.",
            "components": [
                {"id": "army", "name": "Royal Thai Army", "codes": ["rta"]},
                {"id": "navy", "name": "Royal Thai Navy", "codes": ["rtn"]},
                {"id": "air_force", "name": "Royal Thai Air Force", "codes": ["rtaf"]},
            ],
            "installations": inst_out,
            "ranges": [],
            "states": {},
            "national": {
                "personnel": None,
                "spending": None,
                "veterans": None,
                "armed_forces_resident": None,
            },
            "cities": cities_mil,
        },
    )
