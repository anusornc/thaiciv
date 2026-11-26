"""Unit tests for thaiciv pipeline: projection, hex grid, province canonicalization, and web/data contracts."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from pipeline.check import run_checks
from pipeline.core.geo import Albers
from pipeline.core.hexgrid import HexGrid
from pipeline.core.paths import WEB_DATA
from pipeline.core.thailand import BY_CODE, PROVINCES, resolve_province


class TestThailandReference(unittest.TestCase):
    def test_77_provinces(self):
        self.assertEqual(len(PROVINCES), 77)
        self.assertEqual(len(BY_CODE), 77)

    def test_aliases_and_thai_names(self):
        self.assertEqual(resolve_province("Bangkok"), "10")
        self.assertEqual(resolve_province("กรุงเทพมหานคร"), "10")
        self.assertEqual(resolve_province("TH-50"), "50")
        self.assertEqual(resolve_province("0401 - CHON BURI"), "20")
        self.assertEqual(resolve_province("0606 - PHRA NAKHON SRI AYUTHAYA"), "14")
        self.assertEqual(resolve_province("0119 - AMNAT CHAREON"), "37")
        self.assertEqual(resolve_province("0408 - SA KAEW"), "27")
        self.assertEqual(resolve_province("0503 - PHACHUAP KHIRI KHAN"), "77")
        self.assertEqual(resolve_province("จังหวัดเชียงใหม่"), "50")


class TestProjectionAndHexGrid(unittest.TestCase):
    def test_albers_roundtrip_bangkok(self):
        albers = Albers()
        x, y = albers(100.5018, 13.7563)
        lon, lat = albers.inverse(x, y)
        self.assertAlmostEqual(lon, 100.5018, places=4)
        self.assertAlmostEqual(lat, 13.7563, places=4)

    def test_hexgrid_roundtrip(self):
        g = HexGrid(8.0, 85, 163)
        for col, row in ((0, 0), (10, 15), (42, 80), (84, 162)):
            idx = g.index(col, row)
            cx, cy = g.center(col, row)
            self.assertEqual(g.cell_at(cx, cy), idx)
            self.assertAlmostEqual(g.cx(idx), cx, places=6)
            self.assertAlmostEqual(g.cy(idx), cy, places=6)


class TestBuiltWebData(unittest.TestCase):
    def test_pipeline_checks_pass(self):
        if not (WEB_DATA / "world.json").exists():
            self.skipTest("web/data not built")
        lines, fails = run_checks(WEB_DATA)
        self.assertEqual(fails, 0, f"pipeline check failed: {[m for l, m in lines if l == 'FAIL']}")

    def test_bangkok_and_phuket_specializations(self):
        if not (WEB_DATA / "districts.json").exists():
            self.skipTest("web/data not built")
        cities = json.loads((WEB_DATA / "cities.json").read_text(encoding="utf-8"))
        districts = json.loads((WEB_DATA / "districts.json").read_text(encoding="utf-8"))["cities"]
        self.assertEqual(len(cities), 77)
        bkk = next(c for c in cities if c["id"] == "10")
        self.assertTrue(bkk["capital"])
        self.assertGreater(bkk["gdp"], 5e12)  # Bangkok GPP > 5 trillion THB
        self.assertEqual(districts["10"]["badge"]["label"], "Capital city")
        self.assertIn("entertainment_complex", [d["id"] for d in districts["83"]["districts"]])  # Phuket
        self.assertIn("industrial_zone", [d["id"] for d in districts["21"]["districts"]])        # Rayong

    def test_arsenic_monitoring_data(self):
        p = WEB_DATA / "arsenic.json"
        if not p.exists():
            self.skipTest("arsenic.json not built")
        ars = json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual(ars["summary"]["total_stations"], 23)
        self.assertEqual(ars["summary"]["transboundary_exceeding"], 20)
        self.assertEqual(ars["summary"]["control_exceeding"], 0)
        self.assertGreaterEqual(ars["summary"]["peak_as_mg_l"], 0.05)
        self.assertEqual(len(ars["watchpoints"]), 5)
        self.assertGreaterEqual(len(ars["baseline"]), 20)


if __name__ == "__main__":
    unittest.main()
