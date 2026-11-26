"""Wikidata SPARQL (CC0) queries for Thailand's National Parks, UNESCO sites, Universities, Ports & Military bases."""

from __future__ import annotations

import json
import re
import urllib.parse

from ..core.source import Source, SourceInfo

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

QUERIES = {
    "parks": """
SELECT ?item ?itemLabel ?coord ?area WHERE {
  ?item wdt:P31/wdt:P279* wd:Q46169; wdt:P17 wd:Q869; wdt:P625 ?coord.
  OPTIONAL { ?item wdt:P2046 ?area. }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,th". }
} LIMIT 300
""",
    "unesco": """
SELECT ?item ?itemLabel ?coord ?year WHERE {
  ?item wdt:P1435 wd:Q9259; wdt:P17 wd:Q869; wdt:P625 ?coord.
  OPTIONAL { ?item wdt:P580 ?year. }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,th". }
} LIMIT 50
""",
    "universities": """
SELECT ?item ?itemLabel ?coord ?students ?founded WHERE {
  ?item wdt:P31/wdt:P279* wd:Q3918; wdt:P17 wd:Q869; wdt:P625 ?coord.
  OPTIONAL { ?item wdt:P2196 ?students. }
  OPTIONAL { ?item wdt:P571 ?founded. }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,th". }
} LIMIT 300
""",
    "ports": """
SELECT ?item ?itemLabel ?coord WHERE {
  ?item wdt:P31/wdt:P279* wd:Q44782; wdt:P17 wd:Q869; wdt:P625 ?coord.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,th". }
} LIMIT 100
""",
    "military": """
SELECT ?item ?itemLabel ?coord ?instLabel WHERE {
  VALUES ?cls { wd:Q245016 wd:Q695850 wd:Q1324633 wd:Q18691599 }
  ?item wdt:P31/wdt:P279* ?cls; wdt:P17 wd:Q869; wdt:P625 ?coord.
  OPTIONAL { ?item wdt:P31 ?inst. }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en,th". }
} LIMIT 150
""",
}

_PT_RE = re.compile(r"Point\(\s*([+-]?\d+(?:\.\d+)?)\s+([+-]?\d+(?:\.\d+)?)\s*\)")


def _parse_coord(s: str | None) -> tuple[float, float] | None:
    if not s:
        return None
    m = _PT_RE.search(s)
    if not m:
        return None
    return round(float(m.group(1)), 5), round(float(m.group(2)), 5)


class WikidataThailand(Source):
    info = SourceInfo(
        id="wikidata_thailand",
        title="Wikidata Open Knowledge Graph (Thailand Parks, Universities, UNESCO Sites, Ports & Bases)",
        publisher="Wikidata / Wikimedia Foundation",
        homepage="https://www.wikidata.org/",
        license="CC0 1.0 Public Domain",
        description="Geolocated entities in Thailand from Wikidata SPARQL: national parks, UNESCO World Heritage sites, major research universities, seaports and Royal Thai Armed Forces bases.",
        used_for=["Wonders (parks, universities, UNESCO & landmarks)", "Seaports", "Military installations"],
    )

    def fetch(self, force: bool = False) -> None:
        hdrs = {
            "User-Agent": "thaiciv/0.1 (https://github.com/thaiciv; Thailand open-data strategy map)",
            "Accept": "application/sparql-results+json",
        }
        for name, q in QUERIES.items():
            url = SPARQL_ENDPOINT + "?" + urllib.parse.urlencode({"query": q.strip(), "format": "json"})
            self.download(url, f"{name}.json", force=force, headers=hdrs)

    def _dedup_rows(self, filename: str) -> list[dict]:
        raw = json.loads((self.raw_dir / filename).read_text(encoding="utf-8"))
        seen: dict[str, dict] = {}
        for b in raw.get("results", {}).get("bindings", []):
            qid = b["item"]["value"].rsplit("/", 1)[-1]
            lbl = b.get("itemLabel", {}).get("value", "")
            if not lbl or lbl == qid:
                continue
            pt = _parse_coord(b.get("coord", {}).get("value"))
            if not pt:
                continue
            lon, lat = pt
            if not (97.0 <= lon <= 106.0 and 5.5 <= lat <= 20.6):
                continue
            rec = seen.get(qid)
            if rec is None:
                rec = {"qid": qid, "name": lbl, "lon": lon, "lat": lat}
                seen[qid] = rec
            for k in ("area", "students", "year", "founded", "instLabel"):
                if k in b and k not in rec:
                    rec[k] = b[k]["value"]
        return list(seen.values())

    def process(self) -> dict:
        return {
            "vintage": "Wikidata SPARQL snapshot (2026)",
            "parks": self._dedup_rows("parks.json"),
            "unesco": self._dedup_rows("unesco.json"),
            "universities": self._dedup_rows("universities.json"),
            "ports": self._dedup_rows("ports.json"),
            "military": self._dedup_rows("military.json"),
            "_files": [f"{k}.json" for k in QUERIES],
        }
