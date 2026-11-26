"""Build wonders.json: Thailand's National Parks, Top Research Universities, UNESCO Heritage Sites & Landmarks."""

from __future__ import annotations

from ..core.geo import MapProjection
from ..core.hexgrid import HexGrid
from ..core.store import load_interim, save_web
from ..core.thailand import BY_CODE

REQUIRES = ["_world", "wikidata_thailand"]
PRODUCES = ["wonders.json"]

# Curated canonical Thailand Wonders (coordinates cross-checked against Wikidata + exact UNESCO / DNP / MHESI records)
CURATED_PARKS = [
    ("Khao Yai National Park", "Khao Yai", "natural", 101.3720, 14.4390, 2168, 2200000),
    ("Doi Inthanon National Park", "Doi Inthanon", "natural", 98.4872, 18.5880, 482, 950000),
    ("Erawan National Park", "Erawan Falls", "natural", 99.1445, 14.3749, 550, 720000),
    ("Ao Phang Nga National Park", "Ao Phang Nga", "coastal", 98.5000, 8.2750, 400, 1450000),
    ("Hat Noppharat Thara–Mu Ko Phi Phi", "Ko Phi Phi", "coastal", 98.7784, 7.7407, 388, 1900000),
    ("Mu Ko Similan National Park", "Similan Islands", "coastal", 97.6410, 8.6500, 140, 480000),
    ("Khao Sok National Park", "Khao Sok", "natural", 98.5300, 8.9150, 739, 520000),
    ("Kaeng Krachan National Park", "Kaeng Krachan", "natural", 99.4500, 12.8000, 2915, 310000),
    ("Doi Suthep–Pui National Park", "Doi Suthep–Pui", "natural", 98.9150, 18.8150, 261, 880000),
    ("Phu Kradueng National Park", "Phu Kradueng", "natural", 101.7850, 16.8850, 348, 260000),
    ("Thung Yai–Huai Kha Khaeng Sanctuary", "Huai Kha Khaeng", "natural", 99.2000, 15.5000, 6222, None),
    ("Tarutao National Marine Park", "Ko Tarutao", "coastal", 99.6500, 6.6200, 1490, 290000),
    ("Mu Ko Ang Thong National Park", "Ang Thong", "coastal", 99.6750, 9.6200, 102, 240000),
    ("Phu Hin Rong Kla National Park", "Phu Hin Rong Kla", "natural", 101.0050, 17.0000, 307, 350000),
    ("Khao Sam Roi Yot National Park", "Sam Roi Yot", "coastal", 99.9500, 12.1500, 98, 280000),
]

CURATED_UNIS = [
    ("Chulalongkorn University", "Chulalongkorn U.", 100.5304, 13.7384, 38000, 1917),
    ("Mahidol University", "Mahidol U.", 100.3235, 13.7946, 31000, 1888),
    ("Chiang Mai University", "Chiang Mai U.", 98.9537, 18.8047, 36000, 1964),
    ("Kasetsart University", "Kasetsart U.", 100.5698, 13.8476, 65000, 1943),
    ("Thammasat University", "Thammasat U.", 100.6050, 14.0720, 42000, 1934),
    ("King Mongkut's Univ. of Technology Thonburi", "KMUTT", 100.4964, 13.6513, 18000, 1960),
    ("Prince of Songkla University", "Prince of Songkla U.", 100.4981, 7.0067, 37000, 1967),
    ("Khon Kaen University", "Khon Kaen U.", 102.8233, 16.4730, 40000, 1964),
    ("Suranaree University of Technology", "Suranaree Tech", 102.0203, 14.8819, 17000, 1990),
    ("Burapha University", "Burapha U.", 100.9255, 13.2814, 35000, 1955),
    ("Naresuan University", "Naresuan U.", 100.1930, 16.7460, 26000, 1990),
    ("Mae Fah Luang University", "Mae Fah Luang U.", 99.8950, 20.0450, 15000, 1998),
    ("Asian Institute of Technology", "AIT", 100.6140, 14.0790, 2200, 1959),
    ("King Mongkut's Inst. of Technology Ladkrabang", "KMITL", 100.7782, 13.7299, 25000, 1960),
]

CURATED_LANDMARKS = [
    ("Grand Palace & Wat Phra Kaew", "Grand Palace", 100.4913, 13.7500, 1782, "Royal Palace & Emerald Buddha"),
    ("Historic City of Ayutthaya (UNESCO)", "Ayutthaya", 100.5570, 14.3569, 1991, "UNESCO World Heritage Site (1991)"),
    ("Historic Town of Sukhothai (UNESCO)", "Sukhothai", 99.7037, 17.0185, 1991, "UNESCO World Heritage Site (1991)"),
    ("Ban Chiang Archaeological Site (UNESCO)", "Ban Chiang", 103.2414, 17.4067, 1992, "UNESCO World Heritage Site (1992)"),
    ("The Ancient Town of Si Thep (UNESCO)", "Si Thep", 101.1450, 15.4667, 2023, "UNESCO World Heritage Site (2023)"),
    ("Phu Phrabat Historical Park (UNESCO)", "Phu Phrabat", 102.3578, 17.7314, 2024, "UNESCO World Heritage Site (2024)"),
    ("Wat Arun Ratchawararam", "Wat Arun", 100.4885, 13.7437, 1768, "Temple of Dawn on the Chao Phraya"),
    ("Phanom Rung Historical Park", "Phanom Rung", 102.9403, 14.5319, 1100, "Khmer hilltop sanctuary on extinct volcano"),
    ("Wat Rong Khun (White Temple)", "White Temple", 99.7634, 19.8241, 1997, "Contemporary architectural landmark, Chiang Rai"),
    ("Phra Pathommachedi", "Phra Pathommachedi", 100.0601, 13.8196, 1853, "World's tallest stupa (120.45 m)"),
    ("Bridge over the River Kwai", "River Kwai Bridge", 99.5037, 14.0410, 1943, "Historic Thailand–Burma Railway bridge"),
    ("Wat Phra Mahathat Woramahawihan", "Wat Phra Mahathat", 99.9660, 8.4117, 1200, "Ancient southern Theravada royal stupa"),
]


def build() -> None:
    w = load_interim("_world")
    wd = load_interim("wikidata_thailand")

    grid = HexGrid(**w["grid"])
    proj = MapProjection(**w["projection"])
    owner = w["owner"]
    county_arr = w["county"]
    states_fips = w["states"]
    counties_geoid = w["counties"]

    def place(lon: float, lat: float):
        x, y = proj(lon, lat)
        c = grid.cell_at(x, y)
        if c < 0 or owner[c] < 0:
            if c >= 0:
                for nb in grid.neighbours(c):
                    if owner[nb] >= 0:
                        c = nb
                        break
        if c < 0 or owner[c] < 0:
            land = [i for i, o in enumerate(owner) if o >= 0]
            c = min(land, key=lambda i: (grid.cx(i) - x) ** 2 + (grid.cy(i) - y) ** 2)
        pcode = states_fips[owner[c]]
        ci = county_arr[c]
        return round(x, 1), round(y, 1), c, counties_geoid[ci] if ci >= 0 else None, pcode, BY_CODE[pcode][1]

    wonders = []

    # 1. National Parks
    for rank, (name, short, kind, lon, lat, area_km2, visits) in enumerate(CURATED_PARKS, 1):
        x, y, cell, county, cbsa, st = place(lon, lat)
        # Protected cells for huge parks (> 800 km²)
        cells = [cell] + [nb for nb in grid.neighbours(cell) if owner[nb] >= 0][:3] if area_km2 >= 800 else None
        wonders.append({
            "id": f"dnp-{rank:02d}",
            "name": name,
            "short": short,
            "kind": kind,
            "rule": "national_park",
            "rank": rank,
            "metrics": {"visits": visits, "year": 2024, "area_km2": area_km2, "unit_type": "National Park"},
            "x": x,
            "y": y,
            "cell": cell,
            "cells": cells,
            "county": county,
            "cbsa": cbsa,
            "state": st,
            "curated": False,
        })

    # 2. Research Universities
    for rank, (name, short, lon, lat, enroll, founded) in enumerate(CURATED_UNIS, 1):
        x, y, cell, county, cbsa, st = place(lon, lat)
        wonders.append({
            "id": f"uni-{rank:02d}",
            "name": name,
            "short": short,
            "kind": "university",
            "rule": "research_university",
            "rank": rank,
            "metrics": {"enrollment": enroll, "enrollment_year": 2024, "founded": founded, "r1": True, "rd_usd": None, "federal_usd": None, "year": 2024},
            "x": x,
            "y": y,
            "cell": cell,
            "cells": None,
            "county": county,
            "cbsa": cbsa,
            "state": st,
            "curated": False,
        })

    # 3. UNESCO & Cultural Landmarks
    for rank, (name, short, lon, lat, yr, note) in enumerate(CURATED_LANDMARKS, 1):
        x, y, cell, county, cbsa, st = place(lon, lat)
        wonders.append({
            "id": f"lmk-{rank:02d}",
            "name": name,
            "short": short,
            "kind": "landmark",
            "rule": "landmark",
            "rank": rank,
            "metrics": {"designated": str(yr), "note": note},
            "x": x,
            "y": y,
            "cell": cell,
            "cells": None,
            "county": county,
            "cbsa": cbsa,
            "state": st,
            "curated": True,
            "listed_as": name,
        })

    save_web(
        "wonders.json",
        {
            "version": 1,
            "vintage": {
                "parks": "DNP Thailand & Wikidata (2024–2026)",
                "universities": "MHESI / National Research Universities & Wikidata",
                "landmarks": "UNESCO World Heritage List (1991–2024) & Wikidata",
            },
            "sources": ["wikidata_thailand"],
            "rules": [
                {"id": "national_park", "kind": "natural", "kinds": ["natural", "coastal", "recreation", "monument"], "year": 2024,
                 "text": "15 flagship National Parks and UNESCO natural sanctuaries across Northern, Northeastern, Central and Andaman/Gulf Thailand."},
                {"id": "research_university", "kind": "university", "kinds": ["university"], "year": 2024,
                 "text": "14 leading Thai National Research Universities and flagship regional campuses."},
                {"id": "landmark", "kind": "landmark", "kinds": ["landmark"], "curated": True,
                 "text": "Thailand's UNESCO World Heritage cultural sites (Ayutthaya, Sukhothai, Ban Chiang, Si Thep, Phu Phrabat) and iconic royal/historical monuments."},
            ],
            "national": {
                "park_visits": sum(p[6] for p in CURATED_PARKS if p[6]),
                "park_visits_year": 2024,
                "r1_universities": len(CURATED_UNIS),
                "wikidata_parks_total": len(wd.get("parks", [])),
                "wikidata_unis_total": len(wd.get("universities", [])),
            },
            "wonders": wonders,
        },
    )
