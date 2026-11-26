"""Natural Earth 1:10m vectors clipped to Thailand and surrounding Southeast Asia (v5.1.2)."""

from __future__ import annotations

from ..core.geo import bbox_intersects, geojson_lines, geojson_rings, load_geojson
from ..core.source import Source, SourceInfo

NE_BASE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson"
BBOX = (94.0, 3.0, 108.5, 22.5)  # Thailand + Myanmar, Laos, Cambodia, Malaysia, Vietnam margins


class NaturalEarthBase(Source):
    info = SourceInfo(
        id="natural_earth",
        title="Natural Earth 1:10m Physical & Cultural Vectors (v5.1.2)",
        publisher="Natural Earth",
        homepage="https://www.naturalearthdata.com/",
        license="Public domain",
        description="Neighboring country outlines, major rivers (Mekong, Chao Phraya, Ping, Mun, Chi, Salween), lakes (Songkhla Lake), highways and rail lines.",
        used_for=["Neighboring countries", "Rivers and lakes", "Highways and State Railway of Thailand lines"],
    )

    def fetch(self, force: bool = False) -> None:
        for fn in (
            "ne_10m_admin_0_countries.geojson",
            "ne_10m_rivers_lake_centerlines.geojson",
            "ne_10m_lakes.geojson",
            "ne_10m_roads.geojson",
            "ne_10m_railroads.geojson",
        ):
            self.download(f"{NE_BASE}/{fn}", fn, force=force)

    def process(self) -> dict:
        # 1. Neighboring land (everything except Thailand intersecting BBOX)
        neighbors = []
        for f in load_geojson(self.raw_dir / "ne_10m_admin_0_countries.geojson"):
            p = f.get("properties") or {}
            iso = p.get("ISO_A3") or p.get("ADM0_A3") or ""
            if iso == "THA":
                continue
            rings = [r for r in geojson_rings(f["geometry"]) if bbox_intersects(r, BBOX)]
            if rings:
                neighbors.append({"name": p.get("NAME", iso), "iso": iso, "rings": rings})

        # 2. Rivers (skip lake centerlines)
        rivers = []
        for f in load_geojson(self.raw_dir / "ne_10m_rivers_lake_centerlines.geojson"):
            p = f.get("properties") or {}
            if "Lake" in str(p.get("featurecla", "")):
                continue
            lines = [ln for ln in geojson_lines(f["geometry"]) if bbox_intersects(ln, BBOX)]
            if not lines:
                continue
            rank = int(p.get("scalerank") or 6)
            name = p.get("name") or p.get("name_en") or ""
            for ln in lines:
                rivers.append({"name": name, "rank": rank, "pts": ln})

        # 3. Lakes
        lakes = []
        for f in load_geojson(self.raw_dir / "ne_10m_lakes.geojson"):
            p = f.get("properties") or {}
            rings = [r for r in geojson_rings(f["geometry"]) if bbox_intersects(r, BBOX)]
            if rings:
                lakes.append({"name": p.get("name") or "", "rings": rings})

        # 4. Roads
        roads = []
        for f in load_geojson(self.raw_dir / "ne_10m_roads.geojson"):
            p = f.get("properties") or {}
            if p.get("type") == "Ferry Route":
                continue
            lines = [ln for ln in geojson_lines(f["geometry"]) if bbox_intersects(ln, BBOX)]
            if not lines:
                continue
            srank = int(p.get("scalerank") or 8)
            typ = str(p.get("type") or "")
            # Expressways / major highways (class 0 = primary trunk / Asian Highway, class 1 = major highway)
            cls = 0 if (srank <= 5 or "Major Highway" in typ or "Beltway" in typ) else 1
            if srank > 8:
                continue
            rname = p.get("name") or p.get("namealtt") or None
            for ln in lines:
                roads.append({"cls": cls, "name": rname, "pts": ln})

        # 5. Railroads
        rail = []
        for f in load_geojson(self.raw_dir / "ne_10m_railroads.geojson"):
            p = f.get("properties") or {}
            lines = [ln for ln in geojson_lines(f["geometry"]) if bbox_intersects(ln, BBOX)]
            if not lines:
                continue
            srank = int(p.get("scalerank") or 7)
            tier = 0 if srank <= 5 else 1
            for ln in lines:
                rail.append({"tier": tier, "pts": ln})

        return {
            "vintage": "Natural Earth v5.1.2 (1:10m)",
            "neighbors": neighbors,
            "rivers": rivers,
            "lakes": lakes,
            "roads": roads,
            "rail": rail,
            "_files": [
                "ne_10m_admin_0_countries.geojson",
                "ne_10m_rivers_lake_centerlines.geojson",
                "ne_10m_lakes.geojson",
                "ne_10m_roads.geojson",
                "ne_10m_railroads.geojson",
            ],
        }
