"""Shared yield definitions and NESDC industry labels for Thailand."""

from __future__ import annotations

# 19 official NESDC GPP ISIC sectors
INDUSTRIES = {
    "agriculture": "Agriculture, forestry & fishing",
    "mining": "Mining & quarrying",
    "manufacturing": "Manufacturing",
    "utilities": "Electricity, gas & steam",
    "water_waste": "Water supply & waste management",
    "construction": "Construction",
    "trade": "Wholesale & retail trade",
    "transportation": "Transportation & storage",
    "accommodation": "Hotels, dining & tourism services",
    "information": "Information & communication",
    "finance": "Financial & insurance activities",
    "real_estate": "Real estate activities",
    "professional": "Professional, scientific & technical",
    "admin": "Administrative & support services",
    "public_admin": "Public administration & defence",
    "education": "Education",
    "health": "Human health & social work",
    "arts": "Arts, entertainment & recreation",
    "other": "Other service activities",
}

# Mapping from Civ yields to official NESDC 2024p economic output (THB)
YIELD_DEFS = [
    {
        "key": "food",
        "icon": "y-food",
        "emoji": "🌾",
        "label": "Food",
        "color": "#7fbf3f",
        "unit": "usd",
        "description": "Agriculture, forestry & fishing value added (NESDC GPP, THB).",
    },
    {
        "key": "production",
        "icon": "y-production",
        "emoji": "⚙️",
        "label": "Production",
        "color": "#d98838",
        "unit": "usd",
        "description": "Manufacturing, mining, utilities & construction value added (NESDC GPP, THB).",
    },
    {
        "key": "gold",
        "icon": "y-gold",
        "emoji": "💰",
        "label": "Gold",
        "color": "#e5be4c",
        "unit": "usd",
        "description": "Gross Provincial / Domestic Product at current prices (NESDC GPP, THB).",
    },
    {
        "key": "science",
        "icon": "y-science",
        "emoji": "🔬",
        "label": "Science",
        "color": "#55a8e8",
        "unit": "usd",
        "description": "Information & communications, professional/scientific/technical services & education value added (NESDC GPP, THB).",
    },
    {
        "key": "culture",
        "icon": "y-culture",
        "emoji": "🎭",
        "label": "Culture",
        "color": "#c97be0",
        "unit": "usd",
        "description": "Hospitality, tourism accommodation, dining, arts & recreation value added (NESDC GPP, THB).",
    },
]


def compute_yields(gpp_thb: float | None, sectors: dict[str, float]) -> dict[str, float | None]:
    """Compute the 5 Civilization yields directly from official NESDC sector GPP (THB)."""
    if not sectors and gpp_thb is None:
        return {k: None for k in ("food", "production", "gold", "science", "culture")}
    s = lambda *keys: sum(sectors.get(k, 0.0) or 0.0 for k in keys)
    return {
        "food": round(s("agriculture")),
        "production": round(s("manufacturing", "mining", "utilities", "water_waste", "construction")),
        "gold": round(gpp_thb) if gpp_thb is not None else round(sum(sectors.values())),
        "science": round(s("information", "professional", "education")),
        "culture": round(s("accommodation", "arts")),
    }


def rank_map(rows: list[dict], key_fn) -> dict[str, int | None]:
    """Return {row['id']: 1-based rank} descending, ties broken by population."""
    scored = []
    for r in rows:
        v = key_fn(r)
        if v is not None:
            scored.append((v, r.get("population") or 0, r["id"]))
    scored.sort(key=lambda x: (-x[0], -x[1], x[2]))
    ranks: dict[str, int | None] = {r["id"]: None for r in rows}
    for i, (_, _, rid) in enumerate(scored, 1):
        ranks[rid] = i
    return ranks
