"""ETOPO1 elevation & ocean depth over Thailand and surrounding seas via NOAA ERDDAP."""

from __future__ import annotations

import csv

from ..core.source import Source, SourceInfo

# Thailand spans 5.6°N–20.5°N, 97.3°E–105.6°E; add generous margin for Gulf, Andaman Sea & neighbors.
LAT_MIN, LAT_MAX = 4.0, 22.0
LON_MIN, LON_MAX = 95.5, 107.5
STRIDE = 2  # 2 arc-minute (~3.7 km) — crisp relief across Doi Inthanon & Gulf bathymetry (~5 MB)

ERDDAP_URL = (
    "https://coastwatch.pfeg.noaa.gov/erddap/griddap/etopo180.csv"
    f"?altitude%5B({LAT_MIN}):{STRIDE}:({LAT_MAX})%5D%5B({LON_MIN}):{STRIDE}:({LON_MAX})%5D"
)


class Etopo(Source):
    info = SourceInfo(
        id="etopo",
        title="ETOPO1 1 Arc-Minute Global Relief Model (via NOAA ERDDAP)",
        publisher="NOAA National Centers for Environmental Information (NCEI)",
        homepage="https://www.ncei.noaa.gov/products/etopo-global-relief-model",
        license="Public domain (U.S. Government)",
        description="Global land elevation and ocean bathymetry sampled at 2 arc-minute spacing over Thailand, the Gulf of Thailand and the Andaman Sea.",
        used_for=["Hex elevation", "Hill-shading and mountain relief", "Ocean and shelf depth"],
    )

    def fetch(self, force: bool = False) -> None:
        self.download(ERDDAP_URL, "etopo_thailand.csv", force=force)

    def process(self) -> dict:
        lats: list[float] = []
        lons: list[float] = []
        lat_seen: set[float] = set()
        lon_seen: set[float] = set()
        grid_map: dict[tuple[float, float], int] = {}

        with open(self.raw_dir / "etopo_thailand.csv", encoding="utf-8") as f:
            r = csv.reader(f)
            next(r, None)  # header
            next(r, None)  # units
            for row in r:
                if len(row) < 3:
                    continue
                la = round(float(row[0]), 5)
                lo = round(float(row[1]), 5)
                z = int(round(float(row[2])))
                if la not in lat_seen:
                    lat_seen.add(la)
                    lats.append(la)
                if lo not in lon_seen:
                    lon_seen.add(lo)
                    lons.append(lo)
                grid_map[(la, lo)] = z

        lats.sort()
        lons.sort()
        values = [grid_map.get((la, lo), 0) for la in lats for lo in lons]
        return {
            "vintage": "ETOPO1 (NOAA NCEI, 2-arcmin stride)",
            "lat0": lats[0],
            "lat1": lats[-1],
            "lon0": lons[0],
            "lon1": lons[-1],
            "nlat": len(lats),
            "nlon": len(lons),
            "values": values,
            "_files": ["etopo_thailand.csv"],
        }
