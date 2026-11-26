"""OurAirports global airport directory filtered to Thailand (ISO country = TH)."""

from __future__ import annotations

import csv

from ..core.source import Source, SourceInfo

AIRPORTS_URL = "https://davidmegginson.github.io/ourairports-data/airports.csv"

# Published 2024 annual passenger counts (AOT / Department of Airports / Bangkok Airways) for top Thai airports
# Used solely to rank hub tiers (L/M/S/N) where OurAirports has type=large_airport / medium_airport.
KNOWN_PAX_2024 = {
    "BKK": 62230000,  # Suvarnabhumi (AOT FY2024)
    "DMK": 30490000,  # Don Mueang (AOT FY2024)
    "HKT": 17200000,  # Phuket (AOT FY2024)
    "CNX": 9200000,   # Chiang Mai (AOT FY2024)
    "HDY": 3100000,   # Hat Yai (AOT FY2024)
    "KBV": 2600000,   # Krabi (DOA 2024)
    "USM": 2700000,   # Samui (Bangkok Airways 2024)
    "CEI": 1950000,   # Chiang Rai (AOT FY2024)
    "UTH": 1650000,   # Udon Thani (DOA 2024)
    "URT": 1450000,   # Surat Thani (DOA 2024)
    "KKC": 1400000,   # Khon Kaen (DOA 2024)
    "UBP": 1250000,   # Ubon Ratchathani (DOA 2024)
    "NST": 1150000,   # Nakhon Si Thammarat (DOA 2024)
    "UTP": 620000,    # U-Tapao Rayong-Pattaya
    "PHS": 480000,    # Phitsanulok
    "TST": 420000,    # Trang
    "NNT": 350000,    # Nan Nakhon
    "KOP": 310000,    # Nakhon Phanom
    "ROI": 280000,    # Roi Et
    "BFV": 260000,    # Buri Ram
    "SNO": 240000,    # Sakon Nakhon
    "LPT": 210000,    # Lampang
    "LOE": 190000,    # Loei
    "TDX": 140000,    # Trat
    "THS": 110000,    # Sukhothai
    "MAQ": 130000,    # Mae Sot
    "HHQ": 95000,     # Hua Hin
    "UNN": 85000,     # Ranong
    "CJM": 75000,     # Chumphon
}


class OurAirports(Source):
    info = SourceInfo(
        id="ourairports",
        title="OurAirports Open Aviation Directory (Thailand)",
        publisher="OurAirports (Public Domain)",
        homepage="https://ourairports.com/data/",
        license="Public domain",
        description="Geolocated Thai commercial airports (large and medium airports with scheduled service and IATA codes).",
        used_for=["Airports map layer", "Commerce advisor", "City View transport hubs"],
    )

    def fetch(self, force: bool = False) -> None:
        self.download(AIRPORTS_URL, "airports.csv", force=force)

    def process(self) -> dict:
        airports = []
        with open(self.raw_dir / "airports.csv", encoding="utf-8-sig", errors="replace") as f:
            for row in csv.DictReader(f):
                if row.get("iso_country") != "TH":
                    continue
                atype = row.get("type", "")
                if atype not in ("large_airport", "medium_airport"):
                    continue
                iata = (row.get("iata_code") or "").strip()
                if not iata:
                    continue
                try:
                    lat = float(row["latitude_deg"])
                    lon = float(row["longitude_deg"])
                except (KeyError, ValueError):
                    continue
                pax = KNOWN_PAX_2024.get(iata)
                if atype == "large_airport" or (pax and pax >= 8_000_000):
                    hub = "L"
                elif pax and pax >= 2_000_000:
                    hub = "M"
                elif pax and pax >= 500_000:
                    hub = "S"
                else:
                    hub = "N"
                airports.append({
                    "id": iata,
                    "name": (row.get("name") or "").strip(),
                    "city": (row.get("municipality") or "").strip(),
                    "hub": hub,
                    "enplanements": pax,
                    "lat": round(lat, 5),
                    "lon": round(lon, 5),
                    "type": atype,
                })
        airports.sort(key=lambda a: -(a["enplanements"] or 0))
        return {
            "vintage": "OurAirports (2026) & AOT/DOA FY2024 passenger counts",
            "airports": airports,
            "_files": ["airports.csv"],
        }
