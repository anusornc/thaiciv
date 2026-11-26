"""WRI Global Power Plant Database filtered to Thailand (ISO3 = THA)."""

from __future__ import annotations

import csv

from ..core.source import Source, SourceInfo

GPPD_URL = "https://raw.githubusercontent.com/wri/global-power-plant-database/master/output_database/global_power_plant_database.csv"

FUEL_MAP = {
    "Hydro": "hydro",
    "Gas": "gas_plant",
    "Coal": "coal_plant",
    "Solar": "solar",
    "Wind": "wind",
    "Biomass": "biomass",
    "Oil": "oil_plant",
    "Waste": "biomass",
    "Storage": "battery",
}


class WriPowerPlants(Source):
    info = SourceInfo(
        id="wri_power",
        title="Global Power Plant Database v1.3.0 (Thailand subset)",
        publisher="World Resources Institute (WRI)",
        homepage="https://datasets.wri.org/dataset/globalpowerplantdatabase",
        license="CC BY 4.0",
        description="Geolocated power plants in Thailand including EGAT hydroelectric dams (Bhumibol, Sirikit, Srinagarind), natural gas plants, Mae Moh lignite coal plant, solar farms, wind farms and biomass facilities.",
        used_for=["Energy resource icons on map tiles", "Provincial energy capacity breakdown", "Energy & Resources advisor"],
    )

    def fetch(self, force: bool = False) -> None:
        self.download(GPPD_URL, "global_power_plant_database.csv", force=force)

    def process(self) -> dict:
        plants = []
        with open(self.raw_dir / "global_power_plant_database.csv", encoding="utf-8-sig", errors="replace") as f:
            for row in csv.DictReader(f):
                if row.get("country") != "THA":
                    continue
                try:
                    lat = float(row["latitude"])
                    lon = float(row["longitude"])
                    cap = float(row["capacity_mw"])
                except (KeyError, ValueError):
                    continue
                fuel = row.get("primary_fuel", "").strip()
                rtype = FUEL_MAP.get(fuel)
                if not rtype:
                    continue
                owner = (row.get("owner") or "").strip()
                yr = (row.get("commissioning_year") or "").strip()
                plants.append({
                    "id": row.get("gppd_idnr") or "",
                    "name": (row.get("name") or "").strip(),
                    "type": rtype,
                    "fuel": fuel,
                    "capacity_mw": round(cap, 1),
                    "lat": round(lat, 5),
                    "lon": round(lon, 5),
                    "owner": owner,
                    "year": yr,
                })
        plants.sort(key=lambda x: -x["capacity_mw"])
        return {
            "vintage": "WRI Global Power Plant Database v1.3.0",
            "plants": plants,
            "_files": ["global_power_plant_database.csv"],
        }
