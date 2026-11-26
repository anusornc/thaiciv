"""Thailand administrative boundaries (77 Provinces ADM1 & 928 Districts/Amphoe ADM2) from geoBoundaries."""

from __future__ import annotations

import json
import math
from pathlib import Path

from ..core.geo import geojson_rings, load_geojson
from ..core.source import Source, SourceInfo
from ..core.thailand import BY_CODE, resolve_province

ADM1_META_URL = "https://www.geoboundaries.org/api/current/gbOpen/THA/ADM1/"
ADM2_META_URL = "https://www.geoboundaries.org/api/current/gbOpen/THA/ADM2/"


def _ring_area_km2(ring: list[tuple[float, float]]) -> float:
    """Approximate spherical area of a lon/lat ring in km²."""
    if len(ring) < 3:
        return 0.0
    lat_avg = sum(p[1] for p in ring) / len(ring)
    kx = 111.32 * math.cos(math.radians(lat_avg))
    ky = 110.574
    a = 0.0
    j = len(ring) - 1
    for i in range(len(ring)):
        a += (ring[j][0] * kx) * (ring[i][1] * ky) - (ring[i][0] * kx) * (ring[j][1] * ky)
        j = i
    return abs(a) * 0.5


def _rings_centroid(rings: list[list[tuple[float, float]]]) -> tuple[float, float]:
    best = max(rings, key=lambda r: len(r))
    return (
        round(sum(p[0] for p in best) / len(best), 5),
        round(sum(p[1] for p in best) / len(best), 5),
    )


class ThailandBoundaries(Source):
    info = SourceInfo(
        id="thailand_boundaries",
        title="Thailand Administrative Boundaries (77 Provinces & 928 Districts)",
        publisher="geoBoundaries / Royal Thai Survey Department / OCHA ROAP",
        homepage="https://www.geoboundaries.org/",
        license="ODbL 1.0 (ADM1) / CC BY 3.0 IGO (ADM2)",
        description="Official polygon boundaries for Thailand's 77 provinces (changwat) and 928 districts (amphoe & Bangkok khet).",
        used_for=["Land vs. water mask", "77 province borders", "928 district (amphoe) lookup & land area"],
    )

    def _meta_urls(self, force: bool = False) -> tuple[str, str]:
        m1 = self.download(ADM1_META_URL, "adm1_meta.json", force=force)
        m2 = self.download(ADM2_META_URL, "adm2_meta.json", force=force)
        j1 = json.loads(m1.read_text(encoding="utf-8"))
        j2 = json.loads(m2.read_text(encoding="utf-8"))
        u1 = j1.get("simplifiedGeometryGeoJSON") or j1["gjDownloadURL"]
        u2 = j2.get("simplifiedGeometryGeoJSON") or j2["gjDownloadURL"]
        return u1, u2

    def fetch(self, force: bool = False) -> None:
        u1, u2 = self._meta_urls(force=force)
        self.download(u1, "tha_adm1.geojson", force=force)
        self.download(u2, "tha_adm2.geojson", force=force)

    def process(self) -> dict:
        f1 = self.raw_dir / "tha_adm1.geojson"
        f2 = self.raw_dir / "tha_adm2.geojson"

        provinces = []
        seen_p = set()
        for feat in load_geojson(f1):
            p = feat.get("properties") or {}
            code = (
                resolve_province(p.get("shapeISO"))
                or resolve_province(p.get("shapeName"))
                or resolve_province(p.get("ADM1_EN"))
            )
            if not code or code in seen_p:
                continue
            seen_p.add(code)
            rings = geojson_rings(feat["geometry"])
            if not rings:
                continue
            _, abbr, en, th, region, clon, clat = BY_CODE[code]
            area = round(sum(_ring_area_km2(r) for r in rings), 1)
            provinces.append({
                "fips": code,
                "abbr": abbr,
                "name": en,
                "th_name": th,
                "region": region,
                "cap_lon": clon,
                "cap_lat": clat,
                "area_km2": area,
                "rings": rings,
            })
        provinces.sort(key=lambda x: x["fips"])

        # Build fast province point-in-polygon lookup to assign every ADM2 district to its parent province
        from ..core.geo import Shape, ShapeIndex
        p_shapes = [Shape(pr["rings"]) for pr in provinces]
        p_idx = ShapeIndex(p_shapes, cell_km=0.5)

        districts = []
        seq_by_prov: dict[str, int] = {}
        for feat in load_geojson(f2):
            p = feat.get("properties") or {}
            rings = geojson_rings(feat["geometry"])
            if not rings:
                continue
            lon, lat = _rings_centroid(rings)
            pi = p_idx.locate(lon, lat)
            if pi < 0:
                # Fallback: nearest province centroid
                pi = min(
                    range(len(provinces)),
                    key=lambda i: (provinces[i]["cap_lon"] - lon) ** 2 + (provinces[i]["cap_lat"] - lat) ** 2,
                )
            pcode = provinces[pi]["fips"]
            pabbr = provinces[pi]["abbr"]
            seq_by_prov[pcode] = seq_by_prov.get(pcode, 0) + 1
            raw_id = str(p.get("shapeID") or f"{pcode}{seq_by_prov[pcode]:02d}")
            # Canonical 4-digit synthetic or clean geoid: "<pcode><seq:02d>"
            geoid = f"{pcode}{seq_by_prov[pcode]:02d}"
            name = (p.get("shapeName") or f"District {geoid}").strip()
            area = round(sum(_ring_area_km2(r) for r in rings), 1)
            districts.append({
                "geoid": geoid,
                "shape_id": raw_id,
                "name": name,
                "state": pabbr,
                "state_fips": pcode,
                "lon": lon,
                "lat": lat,
                "area_km2": area,
                "rings": rings,
            })
        districts.sort(key=lambda d: (d["state_fips"], d["name"]))

        return {
            "vintage": "geoBoundaries gbOpen THA ADM1/ADM2",
            "provinces": provinces,
            "districts": districts,
            "_files": ["tha_adm1.geojson", "tha_adm2.geojson"],
        }
