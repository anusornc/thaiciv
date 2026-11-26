"""Build world.json and _world interim: Thailand 8 km Albers hex grid with ETOPO1 relief, ESA WorldCover & Natural Earth rivers."""

from __future__ import annotations

import math
from collections import Counter

from ..core.geo import Albers, MapProjection, Shape, ShapeIndex
from ..core.hexgrid import HexGrid
from ..core.store import load_interim, save_interim, save_web

REQUIRES = ["thailand_boundaries", "etopo", "esa_worldcover", "natural_earth"]
PRODUCES = ["_world", "world.json"]

HEX_RADIUS_KM = 8.0   # ~166 km² per hex → ~3,100 Thailand land hexes, crisp islands & all 77 provinces
MARGIN_KM = 140.0

WATER_TABLE = [
    {"id": 0, "name": "Land"},
    {"id": 1, "name": "Ocean", "color": "#1a4267", "rule": "Andaman Sea & deep water (> 80 m depth)"},
    {"id": 2, "name": "Coast", "color": "#286588", "rule": "Gulf of Thailand & coastal waters next to land or shallower than 80 m"},
    {"id": 3, "name": "Lake", "color": "#2f6e92", "rule": "Major inland water bodies (Songkhla Lake, reservoirs)"},
]

RELIEF_TABLE = [
    {"id": 0, "name": "Flat", "rule": "Lowland plains, Chao Phraya basin, Khorat Plateau & river deltas"},
    {"id": 1, "name": "Hills", "rule": "Foothills and uplands (roughness ≥ 55 m or elevation ≥ 350 m)"},
    {"id": 2, "name": "Mountains", "rule": "Mountain ranges: Thanon Thong Chai, Tenasserim, Phetchabun & Sankamphaeng (roughness ≥ 160 m or elevation ≥ 900 m)"},
    {"id": 3, "name": "Peaks", "rule": "Highest summits including Doi Inthanon & northern ridges (max elevation ≥ 1,600 m and high relief)"},
]

COVER_TABLE = [
    {"id": 0, "key": "none", "name": "None", "color": None, "rule": "Water or outside coverage"},
    {"id": 1, "key": "forest_deciduous", "name": "Monsoon & deciduous forest", "color": "#4f7a35", "rule": "ESA WorldCover tree cover (class 10) in drier northern & northeastern basins"},
    {"id": 2, "key": "forest_evergreen", "name": "Tropical rainforest", "color": "#2e6432", "rule": "ESA WorldCover tree cover (class 10) in southern peninsula, eastern coast & highland ridges"},
    {"id": 3, "key": "forest_mixed", "name": "Mixed tropical forest", "color": "#3d6e34", "rule": "ESA WorldCover tree cover (class 10) in transitional uplands"},
    {"id": 4, "key": "scrub", "name": "Shrubland", "color": "#a69964", "rule": "ESA WorldCover shrubland (class 20)"},
    {"id": 5, "key": "grassland", "name": "Grassland & savanna", "color": "#879c52", "rule": "ESA WorldCover grassland (class 30)"},
    {"id": 6, "key": "pasture", "name": "Orchards & rubber mosaic", "color": "#7b9c46", "rule": "Mixed agricultural plantations"},
    {"id": 7, "key": "cropland", "name": "Rice & cropland", "color": "#b4a952", "rule": "ESA WorldCover cropland (class 40): Chao Phraya & Isan rice paddies, cassava, sugarcane"},
    {"id": 8, "key": "wetland", "name": "Mangroves & wetland", "color": "#467a69", "rule": "ESA WorldCover herbaceous wetland (90) & coastal mangroves (95)"},
    {"id": 9, "key": "urban", "name": "Built-up urban", "color": "#948678", "rule": "ESA WorldCover built-up (class 50) ≥ 22% of land samples"},
    {"id": 10, "key": "barren", "name": "Bare ground", "color": "#b8aa8c", "rule": "ESA WorldCover bare / sparse vegetation (class 60)"},
    {"id": 11, "key": "ice", "name": "Snow & ice", "color": "#e2e6ea", "rule": "Unused in tropical Thailand"},
]

# 7-point hex sampling pattern (centre + 6 inner ring points at 0.55*R)
_SAMPLE_OFFSETS = [(0.0, 0.0)] + [
    (0.55 * math.cos(math.radians(a)), 0.55 * math.sin(math.radians(a)))
    for a in (0, 60, 120, 180, 240, 300)
]


def _decode_rle(rle: list[int], total: int) -> bytearray:
    out = bytearray(total)
    pos = 0
    for i in range(0, len(rle), 2):
        val = rle[i]
        cnt = rle[i + 1]
        out[pos : pos + cnt] = bytes([val]) * cnt
        pos += cnt
    return out


def _project_rings(rings, proj: MapProjection):
    return [[proj(lon, lat) for lon, lat in r] for r in rings]


def build() -> None:
    tb = load_interim("thailand_boundaries")
    etopo = load_interim("etopo")
    wc = load_interim("esa_worldcover")
    ne = load_interim("natural_earth")

    provinces = tb["provinces"]
    districts = tb["districts"]

    # 1. Compute Albers bounding box of all 77 Thailand provinces
    albers = Albers()
    xs, ys = [], []
    for p in provinces:
        for r in p["rings"]:
            for lon, lat in r:
                x, y = albers(lon, lat)
                xs.append(x)
                ys.append(y)
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    proj = MapProjection(min_x=min_x, max_y=max_y, margin=MARGIN_KM)
    width = round((max_x - min_x) + 2 * MARGIN_KM, 1)
    height = round((max_y - min_y) + 2 * MARGIN_KM, 1)
    grid = HexGrid.covering(width, height, HEX_RADIUS_KM)
    n = grid.size

    # 2. Build spatial indices for provinces, districts, neighboring countries, lakes
    prov_shapes = [Shape(_project_rings(p["rings"], proj)) for p in provinces]
    prov_idx = ShapeIndex(prov_shapes, cell_km=40.0)

    dist_shapes = [Shape(_project_rings(d["rings"], proj)) for d in districts]
    dist_idx = ShapeIndex(dist_shapes, cell_km=25.0)

    foreign_shapes = [Shape(_project_rings(nb["rings"], proj)) for nb in ne["neighbors"]]
    foreign_idx = ShapeIndex(foreign_shapes, cell_km=60.0)

    lake_shapes = [Shape(_project_rings(lk["rings"], proj)) for lk in ne["lakes"]]
    lake_idx = ShapeIndex(lake_shapes, cell_km=40.0)

    # 3. Prepare ETOPO1 lookup
    e_lat0, e_lat1 = etopo["lat0"], etopo["lat1"]
    e_lon0, e_lon1 = etopo["lon0"], etopo["lon1"]
    e_nlat, e_nlon = etopo["nlat"], etopo["nlon"]
    e_vals = etopo["values"]
    e_dlat = (e_lat1 - e_lat0) / max(1, e_nlat - 1)
    e_dlon = (e_lon1 - e_lon0) / max(1, e_nlon - 1)

    def sample_elev(lon: float, lat: float) -> int:
        ri = int(round((lat - e_lat0) / e_dlat))
        ci = int(round((lon - e_lon0) / e_dlon))
        if 0 <= ri < e_nlat and 0 <= ci < e_nlon:
            return e_vals[ri * e_nlon + ci]
        return -1500

    # 4. Prepare ESA WorldCover lookup
    wc_lat0, wc_lon0, wc_step = wc["lat0"], wc["lon0"], wc["step"]
    wc_nlat, wc_nlon = wc["nlat"], wc["nlon"]
    wc_grid = _decode_rle(wc["rle"], wc_nlat * wc_nlon)

    def sample_wc(lon: float, lat: float) -> int:
        ri = int((lat - wc_lat0) / wc_step)
        ci = int((lon - wc_lon0) / wc_step)
        if 0 <= ri < wc_nlat and 0 <= ci < wc_nlon:
            return wc_grid[ri * wc_nlon + ci]
        return 0

    # 5. Populate every hex cell
    owner = [-1] * n
    county = [-1] * n
    county_samples: list[list[int]] = [[] for _ in range(n)]
    elev = [0] * n
    elev_max = [0] * n
    water = [0] * n
    relief = [0] * n
    cover = [0] * n
    pct = {k: [0] * n for k in ("forest", "crop", "pasture", "grass", "shrub", "wetland", "developed")}

    R = grid.radius
    for row in range(grid.rows):
        for col in range(grid.cols):
            idx = grid.index(col, row)
            cx, cy = grid.center(col, row)
            lon, lat = proj.inverse(cx, cy)

            # Determine ownership at center (or majority of 7 samples if center barely misses a thin island/peninsula)
            p_hit = prov_idx.locate(cx, cy)
            if p_hit < 0:
                # Check the 6 inner points for small islands / narrow coastal provinces (Phuket, Samut Songkhram, Samui)
                hits = []
                for ox, oy in _SAMPLE_OFFSETS[1:]:
                    h = prov_idx.locate(cx + ox * R, cy + oy * R)
                    if h >= 0:
                        hits.append(h)
                if len(hits) >= 2:
                    p_hit = Counter(hits).most_common(1)[0][0]

            if p_hit >= 0:
                owner[idx] = p_hit
                # 7 district samples
                cs = []
                for ox, oy in _SAMPLE_OFFSETS:
                    dh = dist_idx.locate(cx + ox * R, cy + oy * R)
                    if dh >= 0:
                        cs.append(dh)
                county_samples[idx] = cs
                county[idx] = cs[0] if cs else -1
                if county[idx] < 0 and cs:
                    county[idx] = Counter(cs).most_common(1)[0][0]
            else:
                if foreign_idx.locate(cx, cy) >= 0:
                    owner[idx] = -2
                else:
                    owner[idx] = -1

            # Sample elevation across 7 points inside the hex
            zs = []
            for ox, oy in _SAMPLE_OFFSETS:
                slo, sla = proj.inverse(cx + ox * R, cy + oy * R)
                zs.append(sample_elev(slo, sla))

            is_lake = owner[idx] >= 0 and lake_idx.locate(cx, cy) >= 0
            if owner[idx] == -1:
                neg = [z for z in zs if z <= 0]
                elev[idx] = round(sum(neg) / len(neg)) if neg else min(0, round(sum(zs) / len(zs)))
                elev_max[idx] = 0
                water[idx] = 2 if elev[idx] > -80 else 1
                continue

            if is_lake:
                water[idx] = 3
                elev[idx] = min(0, round(sum(zs) / len(zs)))
                elev_max[idx] = 0
                continue

            # Land cell (Thailand or neighbor)
            land_zs = [max(0, z) for z in zs]
            mean_z = sum(land_zs) / len(land_zs)
            max_z = max(land_zs)
            var_z = sum((z - mean_z) ** 2 for z in land_zs) / len(land_zs)
            sd_z = math.sqrt(var_z)
            elev[idx] = round(mean_z)
            elev_max[idx] = round(max_z)

            if max_z >= 1600 and sd_z >= 140:
                relief[idx] = 3
            elif mean_z >= 850 or sd_z >= 150:
                relief[idx] = 2
            elif mean_z >= 260 or sd_z >= 52:
                relief[idx] = 1
            else:
                relief[idx] = 0

            # Sample ESA WorldCover at 13 points inside the hex for accurate mixture
            wc_counts: Counter[int] = Counter()
            wc_pts = _SAMPLE_OFFSETS + [
                (0.8 * math.cos(math.radians(a)), 0.8 * math.sin(math.radians(a)))
                for a in (30, 90, 150, 210, 270, 330)
            ]
            for ox, oy in wc_pts:
                slo, sla = proj.inverse(cx + ox * R, cy + oy * R)
                v = sample_wc(slo, sla)
                if v and v != 80:  # exclude open water from land cover mix
                    wc_counts[v] += 1

            tot = sum(wc_counts.values())
            if tot > 0:
                n_forest = wc_counts[10]
                n_shrub = wc_counts[20]
                n_grass = wc_counts[30]
                n_crop = wc_counts[40]
                n_urb = wc_counts[50]
                n_bare = wc_counts[60]
                n_wet = wc_counts[90] + wc_counts[95]

                if owner[idx] >= 0:
                    pct["forest"][idx] = round(100 * n_forest / tot)
                    pct["crop"][idx] = round(100 * n_crop / tot)
                    pct["grass"][idx] = round(100 * n_grass / tot)
                    pct["shrub"][idx] = round(100 * n_shrub / tot)
                    pct["wetland"][idx] = round(100 * n_wet / tot)
                    pct["developed"][idx] = round(100 * n_urb / tot)

                # Dominant cover id
                if n_urb / tot >= 0.22:
                    cover[idx] = 9  # urban
                else:
                    # Forest subtype by Thailand climate: tropical rainforest in South (<12.5°N) or high mountains or Eastern coast
                    if lat < 12.5 or (lon > 101.8 and lat < 13.5) or mean_z >= 600:
                        f_id = 2  # tropical evergreen
                    elif lat > 15.5 and lon > 101.2:
                        f_id = 1  # dry monsoon deciduous (Isan)
                    else:
                        f_id = 3  # mixed tropical forest
                    groups = [
                        (n_forest, f_id),
                        (n_crop, 7),
                        (n_wet, 8),
                        (n_grass, 5),
                        (n_shrub, 4),
                        (n_bare, 10),
                        (n_urb, 9),
                    ]
                    best_n, best_id = max(groups, key=lambda x: x[0])
                    cover[idx] = best_id if best_n > 0 else 7

    # Guarantee every single one of Thailand's 77 provinces owns at least 1 hex (even tiny Samut Songkhram / Phuket)
    owned_provs = {o for o in owner if o >= 0}
    for pi, p in enumerate(provinces):
        if pi not in owned_provs:
            px, py = proj(p["cap_lon"], p["cap_lat"])
            c = grid.cell_at(px, py)
            if c >= 0:
                owner[c] = pi
                water[c] = 0
                if cover[c] == 0:
                    cover[c] = 9 if p["fips"] == "10" else 7

    # Mark water cells adjacent to any land cell as coastal (water = 2)
    for i in range(n):
        if water[i] == 1:
            for nb in grid.neighbours(i):
                if water[nb] == 0:
                    water[i] = 2
                    break

    # 6. Project rivers and clip to map bounds
    rivers = []
    for rv in ne["rivers"]:
        pts_flat: list[float] = []
        any_in = False
        for lon, lat in rv["pts"]:
            x, y = proj(lon, lat)
            if -50 <= x <= width + 50 and -50 <= y <= height + 50:
                any_in = True
            pts_flat.extend((round(x, 1), round(y, 1)))
        if any_in and len(pts_flat) >= 4:
            rivers.append({"name": rv["name"], "rank": rv["rank"], "pts": pts_flat})

    world_states = [
        {"fips": p["fips"], "abbr": p["abbr"], "name": p["name"], "th_name": p["th_name"], "region": p["region"]}
        for p in provinces
    ]
    world_counties = [
        {"geoid": d["geoid"], "name": d["name"], "state": d["state"], "state_fips": d["state_fips"]}
        for d in districts
    ]

    world_out = {
        "version": 2,
        "grid": grid.to_dict(),
        "width": width,
        "height": height,
        "margin": MARGIN_KM,
        "owner": owner,
        "county": county,
        "elev": elev,
        "elev_max": elev_max,
        "water": water,
        "relief": relief,
        "cover": cover,
        "pct": pct,
        "tables": {"water": WATER_TABLE, "relief": RELIEF_TABLE, "cover": COVER_TABLE},
        "states": world_states,
        "counties": world_counties,
        "rivers": rivers,
    }
    save_web("world.json", world_out)

    save_interim(
        "_world",
        {
            "grid": grid.to_dict(),
            "width": width,
            "height": height,
            "projection": proj.to_dict(),
            "owner": owner,
            "county": county,
            "county_samples": county_samples,
            "states": [p["fips"] for p in provinces],
            "counties": [d["geoid"] for d in districts],
            "water": water,
            "cover": cover,
            "pct": pct,
        },
    )
