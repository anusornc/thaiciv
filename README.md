# thaiciv — Thailand as a 4X Strategy Map, Built from Real Public Data

**Live Map:** [https://anusornc.github.io/thaiciv/](https://anusornc.github.io/thaiciv/) · [ภาษาไทย (`#lang=th`)](https://anusornc.github.io/thaiciv/#lang=th) · [Water & Arsenic Crisis (`#advisor=arsenic`)](https://anusornc.github.io/thaiciv/#advisor=arsenic)

A Civilization-style strategy map visualizer for **Thailand (ประเทศไทย)** — covering all **77 provinces (จังหวัด)** and **928 districts (อำเภอ / เขต)** on an **8 km Albers equal-area hex grid**, built from 13 live, verified Thai & global public data sources with zero invented numbers.

Built on top of the MIT-licensed [`usaciv`](https://karpathy.ai/usaciv/) Canvas 2D + ES module visualization engine by Andrej Karpathy.

## What's Inside

- **8 km Hex Map of Thailand (`world.json`)**: 85 × 163 grid (~3,230 Thailand land hexes, ~166 km² each), capturing Bangkok, Phuket, Ko Samui, the Chao Phraya delta, Khorat Plateau, Tenasserim & Doi Inthanon mountain relief, Gulf of Thailand vs. Andaman Sea depth, 44 major rivers (Mekong, Chao Phraya, Ping, Mun, Chi, Salween), and neighboring countries (Myanmar, Laos, Cambodia, Malaysia, Vietnam) in fog of war.
- **Real Yields in Thai Baht (`฿`)**:
  - **Gold**: Gross Provincial Product (NESDC GPP 2024p — ฿18.68T nationwide, ฿6.35T Bangkok).
  - **Food**: Agriculture, forestry & fishing GPP.
  - **Production**: Manufacturing, mining, utilities & construction GPP.
  - **Science**: Information/communications, professional/scientific/technical & education GPP.
  - **Culture**: Accommodation, dining, tourism, arts & recreation GPP.
- **21 Interactive Map Lenses**: Population density, 2021–2025 growth, non-Thai residents, internal migration, household monthly income, GPP per capita, household debt, spending/income burden, manufacturing share, tourism share, agriculture share, tech/science share, homeownership, unemployment, business density, DOPA village disaster risks, **Arsenic (As · rivers)** surface-water contamination, religious heritage, and true 8 km satellite forest/cropland/urban cover (ESA WorldCover 2021).
- **Thailand Transboundary Arsenic Crisis Layer & Advisor (`#advisor=arsenic`)**:
  - **23 official monitoring stations × 8 rounds** across the Kok, Sai, Ruak, Mekong & 3 Thai-origin control tributaries (`chiangrai.gdcatalog.go.th` / PCD), plus the **2017–2025 Kok River historical baseline** (`KK01`) and **5 national watchpoints** (Mae Ai, Salween, Ron Phibun, Chatree/Phichit, Ban Rai).
  - Toggleable `Arsenic (As)` map layer color-coded against Thailand's `0.010 mg/L` surface-water standard, `Arsenic (As · rivers)` lens (monitored hexes only; unmonitored hexes transparently shown as `no data`), and dedicated **Water & Arsenic Advisor ("Guardian of Rivers")** with river comparison, 8-round trend chart, 2017–2025 baseline bars, filterable/sortable station table, and national watchpoint navigator.
- **City View for all 77 Provincial Hubs**: Industry specialization **Districts** & **City-Type Badges** computed via Location Quotients from NESDC's 19-sector GPP (e.g., *Bangkok — Capital city*, *Phuket — Resort & tourism city*, *Chon Buri & Ayutthaya — Factory powerhouse*, *Rayong — Mining & energy hub*, *Khon Kaen — University city*), Citizen figure rows, GPP sector breakdown, and peer cities.
- **Tile Improvements, Resources, Wonders & Military**:
  - **65 power plants** (EGAT hydro dams like Bhumibol/Sirikit/Srinagarind, gas stations, Mae Moh coal, solar, wind & biomass from WRI GPPD).
  - **Highways & SRT Railways** rasterized onto hex links (Natural Earth 1:10m).
  - **9 principal ports** (Laem Chabang, Map Ta Phut, Bangkok, Songkhla, Phuket, Ranong, Chiang Saen) & **30+ commercial airports** (OurAirports).
  - **41 Thai Wonders** (15 flagship National Parks, 14 National Research Universities, 12 UNESCO World Heritage & cultural landmarks).
  - **21 Royal Thai Armed Forces installations** (RTA, RTN, RTAF).
  - **20 domestic economic corridors** routed along highway & SRT rail links.
- **11 Advisors & Interactive Data Explorer**: Including **Water & Arsenic** plus slice, filter, sort, and scatter-plot dashboards across all **77 Provinces** and **928 Districts (Amphoe)** linked two-way with the map.
- **Full Bilingual UI & Search (English / ภาษาไทย)**: One-click `EN / ไทย` toggle in the top bar (and shareable `#lang=th` URL hash) switches city banners across all 77 provinces, all 21 map lenses, layer toggles, tooltips, panels, national reports, City View, and Advisors (including the full Water & Arsenic dashboard). Press `/` or `⌘K` to search in either English or Thai at any time.

## Quick Start

Requires [uv](https://docs.astral.sh/uv/) (Python 3.11+, standard library only — zero npm or build step):

```bash
uv run python -m pipeline serve        # http://127.0.0.1:8765
```

To rebuild all data from live official Thai & global sources:

```bash
uv run python -m pipeline all          # fetch → process → build web/data/*.json → check
uv run python -m unittest discover -s tests
```

## Caution to Use & Limitations (ข้อควรระวังในการใช้งาน)

> [!CAUTION]
> **Informational & educational visualization only — not official government, medical, drinking-water safety, emergency, or investment advice.**
> *(เพื่อการเรียนรู้และสำรวจข้อมูลสาธารณะเท่านั้น ไม่ใช่ประกาศทางการของหน่วยงานรัฐ ไม่ใช่คำแนะนำความปลอดภัยน้ำดื่มแบบเรียลไทม์ และไม่ใช่คำแนะนำด้านการแพทย์หรือการลงทุน)*

Please keep the following limitations in mind before citing or acting on any figure in **thaiciv**:

1. **Water Quality & Arsenic Safety (`ข้อควรระวังข้อมูลสารหนู`):**
   - The Arsenic layer and **Water & Arsenic Advisor** display a snapshot of official Chiang Rai / PCD CSV monitoring data (23 stations × 8 rounds + 2017–2025 `KK01` baseline). **Do not use this map to decide whether tap, well, or river water is safe to drink, cook, or irrigate.**
   - Unmonitored provinces/hexes show **`no data`** — this means no unified open-data CSV was available, **not** that the area is safe or uncontaminated.
   - Always check live advisories from the [Pollution Control Department (PCD)](https://www.pcd.go.th/), Provincial Waterworks Authority (PWA), and local Public Health Offices.
2. **Spatial Aggregation (`ความละเอียดเชิงพื้นที่`):**
   - Each hex spans **8 km (~166 km²)**. Provincial indicators (GPP, household income, debt, unemployment, disaster counts) apply at the **province level** and do not capture street-, tambon-, or village-level differences.
3. **Data Vintages & Provisional Figures (`รอบปีข้อมูล`):**
   - Official releases cover different years: NESDC GPP **`2024p`** (preliminary), DOPA civil registration (`2020–2025`, registered population only — excludes unregistered migrants and tourists), NSO Socio-Economic & Labor Force Surveys (`2023–2024`), ESA WorldCover satellite imagery (`2021`), and Chiang Rai / PCD Arsenic monitoring (`2017–2026`).
4. **Analytical Conventions (`ข้อกำหนดการประมวลผล`):**
   - In the Chiang Rai Arsenic CSV, raw `'0'` entries mark **unsampled rounds** (excluded from averages, never treated as `0.000 mg/L`); `'<0.010'` below-detection values are counted as compliant and plotted at half detection limit (`0.005 mg/L`) on trend charts. The 5 purple national watchpoints provide documented context where no unified open-data CSV exists.

### How to Independently Validate the Data

- **In-app verification:** Click **Almanac (`สารานุกรม`) → Caution & Validation** or **Sources** to view every direct download URL, retrieval date, and **SHA-256 checksum**.
- **Full machine-readable manifest:** Inspect [`web/data/sources.json`](web/data/sources.json) (60 checksummed files across 13 sources).
- **Reproduce & run automated integrity checks:**
  ```bash
  uv run python -m pipeline all           # re-fetch from official URLs, rebuild & validate
  uv run python -m unittest discover -s tests -v
  ```

## Public Data Sources & Official Validation References (13 Sources, 60 Checksummed Files)

| Source | Publisher | Official Reference URL (for Validation) | Used For |
|---|---|---|---|
| Gross Regional & Provincial Product (GPP) 1995–2024p | NESDC | [nesdc.go.th](https://www.nesdc.go.th/) · [GPP-2024 Excel](https://www.nesdc.go.th/wp-content/uploads/2026/03/GPP-2024-On-Web-1995-2024.xlsx) | Gold & sector yields, 19-sector GPP, specialization districts & badges |
| Civil Registration Population (2020–2025) | DOPA | [stat.bora.dopa.go.th](https://stat.bora.dopa.go.th/) | 77-province population, 2021–2025 growth, non-Thai residents, 928 districts |
| Household Socio-Economic Survey (SES) & Business Census | NSO | [nso.go.th](https://www.nso.go.th/) · [NSO Open API](https://catalogapi.nso.go.th/) | Monthly income, expenditure, debt, homeownership, migration, establishments |
| Labor Force Survey (77 Provinces), ICT & Religion | NSO | [nso.go.th](https://www.nso.go.th/) · [NSO Open API](https://catalogapi.nso.go.th/) | Employment, unemployment rate, internet & religious heritage context |
| Village-Level Disaster Risk (76 Provinces) | DOPA | [catalog.dopa.go.th](https://catalog.dopa.go.th/dataset/c667e7aa-2e62-4c43-a8e1-dd78cfc0758c) | Flood, drought, storm, fire & landslide hazard exposure |
| Surface-Water Arsenic (As) Monitoring & 2017–2025 Baseline | Chiang Rai Provincial Office / PCD / Chiang Rai PHO | [8-Round CSV Dataset](https://chiangrai.gdcatalog.go.th/dataset/e1fc8a4f-1d5c-4571-aff2-89a35e554a08) · [2017–2025 Baseline Dataset](https://chiangrai.gdcatalog.go.th/dataset/2e5aa282-25db-460c-ac6d-d38c4e1bf468) · [pcd.go.th](https://www.pcd.go.th/) | 23 stations × 8 rounds (Kok, Sai, Ruak, Mekong & Thai controls), 2017–2025 baseline & national watchpoints |
| Thailand ADM1 & ADM2 Boundaries | geoBoundaries / RTSD / OCHA | [geoboundaries.org](https://www.geoboundaries.org/) | 77 province borders & 928 district (amphoe) boundaries |
| ESA WorldCover 10m 2021 v200 | European Space Agency (ESA) | [esa-worldcover.org](https://esa-worldcover.org/) | True satellite land cover per 8 km hex (forest, rice/crop, urban, mangroves) |
| ETOPO1 Global Relief (via ERDDAP) | NOAA NCEI | [ncei.noaa.gov/products/etopo-global-relief-model](https://www.ncei.noaa.gov/products/etopo-global-relief-model) | Elevation, hill-shading, mountain ranges & Gulf/Andaman depth |
| Natural Earth 1:10m v5.1.2 | Natural Earth | [naturalearthdata.com](https://www.naturalearthdata.com/) | Neighbors, rivers, lakes, highways & SRT rail lines |
| Global Power Plant Database v1.3.0 | World Resources Institute (WRI) | [datasets.wri.org/dataset/globalpowerplantdatabase](https://datasets.wri.org/dataset/globalpowerplantdatabase) | Thai power plants (gas, coal, hydro dams, solar, wind, biomass) |
| OurAirports Directory | OurAirports (Public Domain) | [ourairports.com/data](https://ourairports.com/data/) | Thai international & domestic airports |
| Wikidata Open Knowledge Graph | Wikidata (CC0) | [query.wikidata.org](https://query.wikidata.org/) | National parks, universities, UNESCO sites, seaports & bases |

## License

MIT License — see [LICENSE](LICENSE). Built on Andrej Karpathy's MIT-licensed `usaciv` engine. Data remains under each publisher's open-data terms (detailed inside the in-app **Almanac**).
