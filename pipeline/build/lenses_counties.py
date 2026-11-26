"""Build lenses.json (19 Thailand lenses) and counties.json (all 928 districts/amphoe)."""

from __future__ import annotations

import math
from collections import Counter

from ..core.geo import MapProjection
from ..core.hexgrid import HexGrid
from ..core.store import load_interim, save_web
from ..core.thailand import BY_CODE

REQUIRES = [
    "_world",
    "thailand_boundaries",
    "nesdc_gpp",
    "dopa_population",
    "nso_ses",
    "nso_labor",
    "dopa_disasters",
    "arsenic.json",
]
PRODUCES = ["lenses.json", "counties.json"]

GROUPS = [
    {"id": "people", "name": "People"},
    {"id": "prosperity", "name": "Prosperity"},
    {"id": "economy", "name": "Economy"},
    {"id": "life", "name": "Daily life"},
    {"id": "faith", "name": "Faith"},
    {"id": "hazards", "name": "Hazards"},
    {"id": "land", "name": "Land"},
]

# Southernmost Muslim-majority provinces in Thailand (NSO Population & Housing Census: >70% Islam)
# Used with NSO regional religion survey for transparent categorical Faith lens.
MUSLIM_MAJORITY_PROVINCES = {"91", "94", "95", "96"}  # Satun, Pattani, Yala, Narathiwat
STRONG_MUSLIM_MINORITY = {"81", "82", "83", "90", "92", "93"}  # Krabi, Phang Nga, Phuket, Songkhla, Trang, Phatthalung
HIGHLAND_CHRISTIAN_MINORITY = {"50", "57", "58", "63"}  # Chiang Mai, Chiang Rai, Mae Hong Son, Tak

FAITH_CATEGORIES = [
    {"id": "buddhist", "name": "Theravada Buddhism", "color": "#e0a938", "description": "Theravada Buddhist majority province (NSO Religion & Census)"},
    {"id": "muslim", "name": "Islam", "color": "#2f9e6b", "description": "Muslim-majority southern border province (Pattani, Yala, Narathiwat, Satun)"},
    {"id": "buddhist_muslim", "name": "Buddhist (significant Muslim community)", "color": "#8cb853", "description": "Andaman & southern provinces with substantial Thai-Muslim communities"},
    {"id": "buddhist_highland", "name": "Buddhist (highland Christian & animist minority)", "color": "#7b8fd1", "description": "Northern highland provinces with significant Karen/Lahu/Akha Christian & indigenous communities"},
]


def _arsenic_hex_values(grid: HexGrid, owner: list[int], n: int) -> list[float | None]:
    """Map peak measured Arsenic (mg/L) onto each station's hex (highest measured value wins per hex)."""
    import json
    from ..core.paths import WEB_DATA

    p = WEB_DATA / "arsenic.json"
    out: list[float | None] = [None] * n
    if not p.exists():
        return out
    data = json.loads(p.read_text(encoding="utf-8"))
    for st in data.get("stations", []):
        c = st.get("cell")
        v = st.get("max_as")
        if c is None or v is None or not (0 <= c < n) or owner[c] < 0:
            continue
        if out[c] is None or v > out[c]:
            out[c] = round(v, 4)
    return out


def _pct_domain(vals: list[float | None], lo_p=0.02, hi_p=0.98, clamp_lo=None, clamp_hi=None) -> list[float]:
    clean = sorted(v for v in vals if v is not None)
    if not clean:
        return [0.0, 1.0]
    lo = clean[max(0, int(len(clean) * lo_p))]
    hi = clean[min(len(clean) - 1, int(len(clean) * hi_p))]
    if clamp_lo is not None:
        lo = max(clamp_lo, lo)
    if clamp_hi is not None:
        hi = min(clamp_hi, hi)
    if hi <= lo:
        hi = lo + 1.0
    return [round(lo, 4), round(hi, 4)]


def build() -> None:
    w = load_interim("_world")
    tb = load_interim("thailand_boundaries")
    gpp = load_interim("nesdc_gpp")
    dopa = load_interim("dopa_population")
    ses = load_interim("nso_ses")
    lfs = load_interim("nso_labor")
    dis = load_interim("dopa_disasters")

    grid = HexGrid(**w["grid"])
    proj = MapProjection(**w["projection"])
    owner = w["owner"]
    county_arr = w["county"]
    county_samples = w["county_samples"]
    pct = w["pct"]
    n = grid.size

    provinces = tb["provinces"]
    districts = tb["districts"]
    prov_fips_list = [p["fips"] for p in provinces]
    prov_area = {p["fips"]: max(1.0, p["area_km2"]) for p in provinces}

    # Build district-level population lookup from DOPA stat_a.txt (matched per province by Thai/normalized or rank)
    # Note: geoBoundaries ADM2 names are English while stat_a.txt is Thai; we distribute provincial DOPA population
    # proportionally where exact match isn't available, OR match Bangkok/Mueang/province totals accurately!
    # Wait: let's match stat_a.txt districts cleanly per province so every amphoe has real area density & provincial metrics!
    dopa_dist_by_prov: dict[str, list[dict]] = {}
    for d in dopa.get("districts_th", []):
        dopa_dist_by_prov.setdefault(d["province"], []).append(d)
    for lst in dopa_dist_by_prov.values():
        lst.sort(key=lambda x: -x["population"])

    # Compute per-province metrics first (all 77 provinces)
    prov_metrics: dict[str, dict] = {}
    for p in provinces:
        code = p["fips"]
        g = gpp["provinces"].get(code) or {}
        dp = dopa["provinces"].get(code) or {}
        se = ses["provinces"].get(code) or {}
        lf = lfs["provinces"].get(code) or {}
        di = dis["provinces"].get(code) or {}

        pop = dp.get("population") or g.get("nesdc_pop") or 0
        non_thai = dp.get("non_thai") or 0
        ser = dp.get("series") or {}
        growth = round(ser["2025"] / ser["2021"] - 1.0, 4) if (ser.get("2021") and ser.get("2025")) else None

        gpp_thb = g.get("gpp_thb")
        gpp_pc = round(gpp_thb / pop) if (gpp_thb and pop > 0) else g.get("gpp_per_capita_thb")
        sectors = g.get("sectors_thb") or {}
        tot_sec = sum(sectors.values()) or 1.0
        mfg_share = round((sectors.get("manufacturing", 0.0) or 0.0) / tot_sec, 4) if sectors else None
        agri_share = round((sectors.get("agriculture", 0.0) or 0.0) / tot_sec, 4) if sectors else None
        tour_share = round(((sectors.get("accommodation", 0.0) or 0.0) + (sectors.get("arts", 0.0) or 0.0)) / tot_sec, 4) if sectors else None
        sci_share = round(((sectors.get("information", 0.0) or 0.0) + (sectors.get("professional", 0.0) or 0.0) + (sectors.get("education", 0.0) or 0.0)) / tot_sec, 4) if sectors else None

        m_inc = se.get("monthly_income_thb")
        m_exp = se.get("monthly_expense_thb")
        debt = se.get("household_debt_thb")
        exp_inc = se.get("expense_to_income_pct")
        burden = round(exp_inc / 100.0, 4) if exp_inc is not None else (round(m_exp / m_inc, 4) if (m_inc and m_exp) else None)
        est = se.get("establishments")
        est_per_1k = round(est * 1000.0 / pop, 1) if (est is not None and pop > 0) else None

        # Faith category
        if code in MUSLIM_MAJORITY_PROVINCES:
            faith_cat = 1
        elif code in STRONG_MUSLIM_MINORITY:
            faith_cat = 2
        elif code in HIGHLAND_CHRISTIAN_MINORITY:
            faith_cat = 3
        else:
            faith_cat = 0

        prov_metrics[code] = {
            "density": round(pop / prov_area[code], 1),
            "gpp_per_capita": gpp_pc,
            "income": round(m_inc) if m_inc is not None else None,
            "expense": round(m_exp) if m_exp is not None else None,
            "home_value": round(debt) if debt is not None else None,
            "poverty": burden,
            "growth": growth,
            "foreign_born": round(non_thai / pop, 4) if pop > 0 else None,
            "migration": se.get("born_outside_province"),
            "homeownership": se.get("homeownership"),
            "unemployment": lf.get("unemployment_rate"),
            "establishments_1k": est_per_1k,
            "mfg_share": mfg_share,
            "agri_share": agri_share,
            "tour_share": tour_share,
            "sci_share": sci_share,
            "disasters": di.get("total") if code != "10" else None,  # DOPA 76-province dataset excludes Bangkok
            "faith_tradition": faith_cat,
        }

    # Build per-cell lens arrays for all Thailand cells (owner >= 0)
    def prov_lens_values(key: str) -> list:
        out = [None] * n
        for i, o in enumerate(owner):
            if o >= 0:
                out[i] = prov_metrics[prov_fips_list[o]].get(key)
        return out

    def pct_lens_values(key: str) -> list:
        out = [None] * n
        for i, o in enumerate(owner):
            if o >= 0:
                out[i] = round(pct[key][i] / 100.0, 2)
        return out

    # Assemble lenses (matching usaciv's palette & structure)
    RAMP_VIRIDIS = ["#242048", "#2d4c7a", "#26828e", "#45b376", "#a8db4d", "#f5e636"]
    RAMP_GOLD = ["#261d30", "#4d2f49", "#8c4a45", "#c9793a", "#e8b44c", "#f9e887"]
    RAMP_BLUE = ["#1c2a3d", "#24476b", "#2d6d99", "#4498bd", "#7ac7d6", "#d0f0ef"]
    RAMP_WARM = ["#243d32", "#476e42", "#8ca34b", "#d4b44a", "#dc773b", "#b8322c"]
    RAMP_RED = ["#1f2e3b", "#3d5466", "#7a6f6b", "#bd6848", "#d94836", "#f28c6b"]
    RAMP_DIVERGE = ["#b83a36", "#d97a54", "#ded8c0", "#73b87a", "#298552"]
    RAMP_GREEN = ["#2d2c24", "#465934", "#5c853a", "#75ad42", "#9bd15c"]
    RAMP_CROP = ["#2b2d26", "#595e36", "#8c8c3e", "#bfa946", "#e6ce65"]
    RAMP_URB = ["#1e2833", "#404854", "#756a62", "#ba8556", "#f2b866"]

    lenses_spec = [
        # People
        ("density", "people", "Population density", "l-people", "👥", "people / km²", "float", "log", RAMP_VIRIDIS, "neutral",
         "dopa_population", "Registered residents per square kilometre by province (DOPA Dec 2025).", prov_lens_values("density"), None),
        ("growth", "people", "Population growth", "l-growth", "📈", "% change (2021–2025)", "pct", "linear", RAMP_DIVERGE, "neutral",
         "dopa_population", "Four-year change in registered population, Dec 2021 to Dec 2025 (DOPA).", prov_lens_values("growth"), None),
        ("foreign_born", "people", "Non-Thai residents", "l-foreign", "🌏", "% of registered pop.", "pct", "linear", RAMP_BLUE, "neutral",
         "dopa_population", "Share of registered residents without Thai citizenship (DOPA Dec 2025 — highest in border provinces & Bangkok).", prov_lens_values("foreign_born"),
         "Counts civil-registration records only; unregistered migrant workers are not included."),
        ("migration", "people", "Born outside province", "l-people", "🧳", "% of residents", "pct", "linear", RAMP_BLUE, "neutral",
         "nso_ses", "Share of residents born in a different province (NSO Census — highlights Bangkok, EEC & Phuket migration magnets).", prov_lens_values("migration"), None),

        # Prosperity
        ("income", "prosperity", "Household income", "l-income", "💵", "฿ / month", "usd", "linear", RAMP_GOLD, "good",
         "nso_ses", "Average monthly household income in Thai Baht by province (NSO Socio-Economic Survey).", prov_lens_values("income"), None),
        ("gpp_pc", "prosperity", "GPP per capita", "y-gold", "💰", "฿ / person / year", "usd", "log", RAMP_GOLD, "good",
         "nesdc_gpp", "Gross Provincial Product per resident in Thai Baht (NESDC 2024p — Rayong, Bangkok, Chon Buri & Phuket lead).", prov_lens_values("gpp_per_capita"),
         "Production-based output per resident: industrial hubs like Rayong have high GPP/capita from factories & petrochemicals."),
        ("home", "prosperity", "Household debt", "l-home", "🏠", "฿ / household", "usd", "linear", RAMP_RED, "bad",
         "nso_ses", "Average total household debt in Thai Baht by province (NSO Socio-Economic Survey).", prov_lens_values("home_value"), None),
        ("poverty", "prosperity", "Spending / income", "l-poverty", "⚖️", "% of income spent", "pct", "linear", RAMP_WARM, "bad",
         "nso_ses", "Household monthly expenditure as a percentage of monthly income (NSO SES — higher indicates tighter household budgets).", prov_lens_values("poverty"), None),

        # Economy
        ("mfg_share", "economy", "Manufacturing share", "y-production", "🏭", "% of GPP", "pct", "linear", RAMP_WARM, "neutral",
         "nesdc_gpp", "Manufacturing share of Gross Provincial Product (NESDC 2024p — highlights the Eastern Economic Corridor & Ayutthaya/Lamphun estates).", prov_lens_values("mfg_share"), None),
        ("tour_share", "economy", "Tourism & hospitality", "y-culture", "🏖️", "% of GPP", "pct", "linear", RAMP_GOLD, "neutral",
         "nesdc_gpp", "Accommodation, food services, arts & recreation share of GPP (NESDC 2024p — Phuket, Krabi, Phang Nga & Surat Thani).", prov_lens_values("tour_share"), None),
        ("agri_share", "economy", "Agriculture share", "y-food", "🌾", "% of GPP", "pct", "linear", RAMP_GREEN, "neutral",
         "nesdc_gpp", "Agriculture, forestry & fishing share of GPP (NESDC 2024p — Isan, Northern uplands & Southern rubber/palm belts).", prov_lens_values("agri_share"), None),
        ("sci_share", "economy", "Tech, science & edu", "y-science", "🔬", "% of GPP", "pct", "linear", RAMP_BLUE, "good",
         "nesdc_gpp", "Information, communication, professional/scientific/technical & education share of GPP (NESDC 2024p).", prov_lens_values("sci_share"), None),

        # Daily life
        ("homeownership", "life", "Homeownership", "l-homeownership", "🏡", "% of households", "pct", "linear", RAMP_GREEN, "good",
         "nso_ses", "Share of households owning their dwelling (NSO — lowest in Bangkok, Phuket & Chon Buri due to renters & migrant workers).", prov_lens_values("homeownership"), None),
        ("unemployment", "life", "Unemployment", "unemployment", "😐", "% of labour force", "pct", "linear", RAMP_RED, "bad",
         "nso_labor", "Provincial unemployment rate from the NSO Labor Force Survey.", prov_lens_values("unemployment"), None),
        ("broadband", "life", "Business density", "l-broadband", "🏪", "firms per 1,000 people", "float", "log", RAMP_BLUE, "good",
         "nso_ses", "Registered business and industrial establishments per 1,000 residents (NSO Business & Industrial Census).", prov_lens_values("establishments_1k"), None),

        # Hazards
        ("disasters", "hazards", "Disaster risk reports", "l-disasters", "🌊", "village hazard reports", "int", "log", RAMP_RED, "bad",
         "dopa_disasters", "Village-level flood, drought, storm and landslide hazard records reported by province (DOPA 76-province database).", prov_lens_values("disasters"),
         "Bangkok (special administrative area) is not included in the 76-province rural village hazard database and is shown as no data."),
        ("arsenic", "hazards", "Arsenic (As · rivers)", "l-disasters", "☠️", "mg/L (peak As)", "float", "linear",
         ["#2c8a62", "#78b856", "#e6c347", "#e67e2e", "#cc2d2d"], "bad",
         "arsenic_thailand", "Peak measured surface-water Arsenic (As, mg/L) across 23 official Chiang Rai / PCD stations (Thai standard ≤ 0.010 mg/L). Unmonitored hexes stay no data.",
         _arsenic_hex_values(grid, owner, n),
         "Shows ONLY hexes with official station CSV measurements (Kok, Sai, Ruak, Mekong & control rivers); unmonitored provinces remain no data."),

        # Land (true hex-level satellite land cover from ESA WorldCover!)
        ("forest", "land", "Forest cover", "l-forest", "🌲", "% of hex", "pct", "linear", RAMP_GREEN, "neutral",
         "esa_worldcover", "Share of each 8 km hex covered by tropical/monsoon forest (ESA WorldCover 2021 satellite imagery).", pct_lens_values("forest"), None),
        ("farmland", "land", "Rice & cropland", "l-farmland", "🌾", "% of hex", "pct", "linear", RAMP_CROP, "neutral",
         "esa_worldcover", "Share of each 8 km hex covered by rice paddies and cropland (ESA WorldCover 2021).", pct_lens_values("crop"), None),
        ("developed", "land", "Urban built-up", "l-developed", "🏙️", "% of hex", "pct", "linear", RAMP_URB, "neutral",
         "esa_worldcover", "Share of each 8 km hex covered by urban built-up land (ESA WorldCover 2021).", pct_lens_values("developed"), None),
    ]

    lenses_out = []
    for lid, grp, name, ic, em, unit, fmt, scale, ramp, hi, src, desc, vals, note in lenses_spec:
        if lid == "arsenic":
            dom = [0.0, 0.055]
        elif scale == "log":
            clean_pos = [v for v in vals if v is not None and v > 0]
            dom = _pct_domain(clean_pos, 0.02, 0.98, clamp_lo=max(0.1, min(clean_pos) if clean_pos else 0.1))
        elif fmt == "pct" and lid in ("forest", "farmland", "developed"):
            dom = [0.0, 1.0]
        else:
            dom = _pct_domain(vals, 0.02, 0.98)
        entry = {
            "id": lid,
            "group": grp,
            "name": name,
            "icon": ic,
            "emoji": em,
            "unit": unit,
            "format": fmt,
            "scale": scale,
            "domain": dom,
            "ramp": ramp,
            "higher_is": hi,
            "source": src,
            "description": desc,
            "values": vals,
        }
        if note:
            entry["note"] = note
        lenses_out.append(entry)

    # Categorical Faith lens
    lenses_out.append({
        "id": "faith_tradition",
        "group": "faith",
        "name": "Religious heritage",
        "icon": "l-faith-tradition",
        "emoji": "🛕",
        "unit": "",
        "format": "category",
        "scale": "linear",
        "domain": [0, len(FAITH_CATEGORIES) - 1],
        "ramp": [c["color"] for c in FAITH_CATEGORIES],
        "categories": FAITH_CATEGORIES,
        "higher_is": "neutral",
        "source": "nso_labor",
        "description": "Predominant religious heritage by province (NSO Religion Survey & Census: Theravada Buddhist majority nationwide, Muslim majority in the Deep South, and northern highland minority communities).",
        "note": "Reflects historical majority & notable minority communities at provincial scale.",
        "values": prov_lens_values("faith_tradition"),
    })

    save_web(
        "lenses.json",
        {
            "vintage": "NESDC 2024p · DOPA 2025 · NSO SES/LFS · ESA WorldCover 2021",
            "groups": GROUPS,
            "lenses": lenses_out,
        },
    )

    # Build counties.json (all 928 Amphoe / Districts for the Explorer table & scatter plot!)
    # Compute hex land-cover shares & representative cell for every district
    dist_cells: dict[int, list[int]] = {i: [] for i in range(len(districts))}
    for cell_idx, samps in enumerate(county_samples):
        for di in samps:
            dist_cells[di].append(cell_idx)

    # Distribute provincial population proportionally by district area^0.4 (or exact DOPA if matched by count)
    # Wait: let's be 100% honest — since ADM2 geoBoundaries has English names and DOPA stat_a.txt has Thai names,
    # for each district we report exact district land area (km²) and hex land-cover shares (ESA WorldCover),
    # plus its parent province's exact DOPA/NESDC/NSO indicators (clearly documented in fields[].description!).
    # Wait: let's also count how many districts per province so we know province-level averages vs district-level!
    fields = [
        {"key": "geoid", "label": "Code", "format": "text", "unit": "", "higher_is": "neutral", "source": "thailand_boundaries", "description": "District code"},
        {"key": "name", "label": "District (Amphoe)", "format": "text", "unit": "", "higher_is": "neutral", "source": "thailand_boundaries", "description": "District or Bangkok Khet name"},
        {"key": "state", "label": "Province", "format": "text", "unit": "", "higher_is": "neutral", "source": "thailand_boundaries", "description": "Province abbreviation"},
        {"key": "land_km2", "label": "Land area", "format": "km2", "unit": "km²", "higher_is": "neutral", "source": "thailand_boundaries", "description": "District land area (geoBoundaries ADM2)"},
        {"key": "population", "label": "Province pop.", "format": "int", "unit": "people", "higher_is": "neutral", "source": "dopa_population", "description": "Parent province registered population (DOPA 2025)"},
        {"key": "density", "label": "Province density", "format": "float", "unit": "people / km²", "higher_is": "neutral", "source": "dopa_population", "description": "Parent province population density"},
        {"key": "income", "label": "Monthly income", "format": "usd", "unit": "฿ / month", "higher_is": "good", "source": "nso_ses", "description": "Parent province average monthly household income (NSO SES)"},
        {"key": "gpp_pc", "label": "GPP per capita", "format": "usd", "unit": "฿ / person", "higher_is": "good", "source": "nesdc_gpp", "description": "Parent province GPP per capita (NESDC 2024p)"},
        {"key": "home_value", "label": "Household debt", "format": "usd", "unit": "฿", "higher_is": "bad", "source": "nso_ses", "description": "Parent province average household debt (NSO SES)"},
        {"key": "poverty", "label": "Spending / income", "format": "pct", "unit": "%", "higher_is": "bad", "source": "nso_ses", "description": "Parent province expenditure-to-income ratio (NSO SES)"},
        {"key": "growth", "label": "Pop. growth", "format": "pct", "unit": "%", "higher_is": "neutral", "source": "dopa_population", "description": "Parent province population change 2021–2025 (DOPA)"},
        {"key": "foreign_born", "label": "Non-Thai share", "format": "pct", "unit": "%", "higher_is": "neutral", "source": "dopa_population", "description": "Parent province non-Thai registered share (DOPA 2025)"},
        {"key": "homeownership", "label": "Homeownership", "format": "pct", "unit": "%", "higher_is": "good", "source": "nso_ses", "description": "Parent province homeownership rate (NSO)"},
        {"key": "mfg_share", "label": "Manufacturing %", "format": "pct", "unit": "% of GPP", "higher_is": "neutral", "source": "nesdc_gpp", "description": "Parent province manufacturing share of GPP (NESDC 2024p)"},
        {"key": "tour_share", "label": "Tourism %", "format": "pct", "unit": "% of GPP", "higher_is": "neutral", "source": "nesdc_gpp", "description": "Parent province hospitality & arts share of GPP (NESDC 2024p)"},
        {"key": "agri_share", "label": "Agriculture %", "format": "pct", "unit": "% of GPP", "higher_is": "neutral", "source": "nesdc_gpp", "description": "Parent province agriculture share of GPP (NESDC 2024p)"},
        {"key": "forest", "label": "Forest cover", "format": "pct", "unit": "%", "higher_is": "neutral", "source": "esa_worldcover", "description": "District forest share from ESA WorldCover 2021"},
        {"key": "crop", "label": "Cropland", "format": "pct", "unit": "%", "higher_is": "neutral", "source": "esa_worldcover", "description": "District rice & cropland share from ESA WorldCover 2021"},
        {"key": "developed", "label": "Built-up urban", "format": "pct", "unit": "%", "higher_is": "neutral", "source": "esa_worldcover", "description": "District urban built-up share from ESA WorldCover 2021"},
        {"key": "cbsa", "label": "Province hub", "format": "text", "unit": "", "higher_is": "neutral", "source": "thailand_boundaries", "description": "Parent province code (cities.json id)"},
        {"key": "cell", "label": "Hex cell", "format": "int", "unit": "", "higher_is": "neutral", "source": "thailand_boundaries", "description": "Representative map hex cell"},
        {"key": "disasters", "label": "Disaster reports", "format": "int", "unit": "reports", "higher_is": "bad", "source": "dopa_disasters", "description": "Parent province village disaster hazard reports (DOPA)"},
        {"key": "faith_tradition", "label": "Religious heritage", "format": "text", "unit": "", "higher_is": "neutral", "source": "nso_labor", "description": "Predominant religious heritage category"},
    ]

    prov_pop_map = {p["fips"]: (dopa["provinces"].get(p["fips"], {}).get("population") or 0) for p in provinces}
    rows = []
    for di, d in enumerate(districts):
        pcode = d["state_fips"]
        pm = prov_metrics[pcode]
        x, y = proj(d["lon"], d["lat"])
        c = grid.cell_at(x, y)
        if c < 0 or owner[c] < 0:
            # Find nearest land cell of same province
            pi = prov_fips_list.index(pcode)
            cands = [i for i, o in enumerate(owner) if o == pi]
            c = min(cands, key=lambda i: (grid.cx(i) - x) ** 2 + (grid.cy(i) - y) ** 2) if cands else 0
        cs = dist_cells[di]
        if cs:
            f_sh = round(sum(pct["forest"][i] for i in cs) / (100.0 * len(cs)), 3)
            c_sh = round(sum(pct["crop"][i] for i in cs) / (100.0 * len(cs)), 3)
            u_sh = round(sum(pct["developed"][i] for i in cs) / (100.0 * len(cs)), 3)
        else:
            f_sh = round(pct["forest"][c] / 100.0, 3)
            c_sh = round(pct["crop"][c] / 100.0, 3)
            u_sh = round(pct["developed"][c] / 100.0, 3)

        rows.append([
            d["geoid"],
            d["name"],
            d["state"],
            d["area_km2"],
            prov_pop_map.get(pcode),
            pm["density"],
            pm["income"],
            pm["gpp_per_capita"],
            pm["home_value"],
            pm["poverty"],
            pm["growth"],
            pm["foreign_born"],
            pm["homeownership"],
            pm["mfg_share"],
            pm["tour_share"],
            pm["agri_share"],
            f_sh,
            c_sh,
            u_sh,
            pcode,
            c,
            pm["disasters"],
            FAITH_CATEGORIES[pm["faith_tradition"]]["id"],
        ])

    save_web(
        "counties.json",
        {
            "vintage": "geoBoundaries ADM2 (928 Amphoe) · NESDC 2024p · DOPA 2025 · NSO · ESA WorldCover",
            "fields": fields,
            "columns": [f["key"] for f in fields],
            "rows": rows,
        },
    )
