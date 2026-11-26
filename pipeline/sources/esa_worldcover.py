"""ESA WorldCover 10m v200 (2021) land cover over Thailand via Cloud-Optimized GeoTIFF overviews.

Reads the built-in 562x562 (~600 m) overview tile (IFD 6) from each 3°x3° public AWS S3
Cloud-Optimized GeoTIFF using pure-Python HTTP Range requests + zlib — zero external
libraries and ~1.5 MB total download for all of Thailand and its neighbors.
"""

from __future__ import annotations

import json
import struct
import urllib.error
import zlib

from ..core import fetch
from ..core.source import Source, SourceInfo

S3_BASE = "https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/map"

# 3°×3° tiles covering Thailand (5.6°N–20.5°N, 97.3°E–105.6°E) + neighbors
TILE_LATS = [3, 6, 9, 12, 15, 18]
TILE_LONS = [96, 99, 102, 105]


def _tile_name(lat: int, lon: int) -> str:
    return f"N{lat:02d}E{lon:03d}"


def _tile_url(lat: int, lon: int) -> str:
    return f"{S3_BASE}/ESA_WorldCover_10m_2021_v200_{_tile_name(lat, lon)}_Map.tif"


def _parse_ifd6_range(hdr: bytes) -> tuple[int, int, int, int, int, int] | None:
    """Return (width, height, tile_w, tile_h, tile_offset, tile_bytes) for the smallest overview IFD."""
    if len(hdr) < 8:
        return None
    endian = "<" if hdr[:2] == b"II" else ">"
    magic = struct.unpack(endian + "H", hdr[2:4])[0]
    if magic != 42:
        return None
    off = struct.unpack(endian + "I", hdr[4:8])[0]
    last_good = None
    while off and off + 2 < len(hdr):
        n = struct.unpack(endian + "H", hdr[off : off + 2])[0]
        tags = {}
        pos = off + 2
        for _ in range(n):
            if pos + 12 > len(hdr):
                break
            tag, typ, cnt, val = struct.unpack(endian + "HHII", hdr[pos : pos + 12])
            tags[tag] = (typ, cnt, val)
            pos += 12
        w = tags.get(256, (0, 0, 0))[2]
        h = tags.get(257, (0, 0, 0))[2]
        tw = tags.get(322, (0, 0, 0))[2]
        th = tags.get(323, (0, 0, 0))[2]
        comp = tags.get(259, (0, 0, 0))[2]
        toff_tag = tags.get(324)
        tbc_tag = tags.get(325)
        if toff_tag and tbc_tag and toff_tag[1] == 1 and comp == 8:
            last_good = (w, h, tw, th, toff_tag[2], tbc_tag[2])
        off = struct.unpack(endian + "I", hdr[pos : pos + 4])[0] if pos + 4 <= len(hdr) else 0
    return last_good


class EsaWorldCover(Source):
    info = SourceInfo(
        id="esa_worldcover",
        title="ESA WorldCover 10m 2021 v200 (COG Overview Pyramid)",
        publisher="European Space Agency (ESA) WorldCover Consortium",
        homepage="https://esa-worldcover.org/",
        license="CC BY 4.0",
        description="Global satellite land-cover classification (tree cover, cropland, shrubland, grassland, built-up, wetlands, mangroves, water) sampled from the 562×562 (~600 m) overview of each 3°×3° Cloud-Optimized GeoTIFF over Thailand.",
        used_for=["Dominant land cover per hex", "Forest, cropland, wetland and built-up shares", "Land cover lenses"],
    )

    def fetch(self, force: bool = False) -> None:
        meta_file = self.raw_dir / "tiles_meta.json"
        if meta_file.exists() and not force:
            # Verify cached tiles exist
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
            if all((self.raw_dir / t["bin"]).exists() for t in meta["tiles"]):
                return
        tiles_meta = []
        for lat in TILE_LATS:
            for lon in TILE_LONS:
                tag = _tile_name(lat, lon)
                url = _tile_url(lat, lon)
                hdr_rel = f"{tag}.hdr"
                try:
                    hdr_path = self.download(url, hdr_rel, force=force, headers={"Range": "bytes=0-65535"})
                except urllib.error.HTTPError as e:
                    if e.code in (403, 404):
                        continue  # pure ocean tile not published in ESA WorldCover
                    raise
                info = _parse_ifd6_range(hdr_path.read_bytes())
                if not info:
                    continue
                w, h, tw, th, toff, tbc = info
                bin_rel = f"{tag}.zlib"
                self.download(
                    url,
                    bin_rel,
                    force=force,
                    headers={"Range": f"bytes={toff}-{toff + tbc - 1}"},
                )
                tiles_meta.append({
                    "tag": tag,
                    "lat0": lat,
                    "lon0": lon,
                    "lat1": lat + 3,
                    "lon1": lon + 3,
                    "w": w,
                    "h": h,
                    "tw": tw,
                    "th": th,
                    "hdr": hdr_rel,
                    "bin": bin_rel,
                })
        meta_file.parent.mkdir(parents=True, exist_ok=True)
        meta_file.write_text(json.dumps({"tiles": tiles_meta}, indent=2), encoding="utf-8")

    def process(self) -> dict:
        meta = json.loads((self.raw_dir / "tiles_meta.json").read_text(encoding="utf-8"))
        # Downsample each 562x562 tile by 2x → 281x281 (~1.2 km per pixel) into a single compact raster
        # covering [3..21°N] × [96..108°E] at 0.0125° (~1.38 km) grid → 1440 rows × 960 cols!
        lat0, lat1 = 3.0, 21.0
        lon0, lon1 = 96.0, 108.0
        step = 0.02  # ~2.2 km grid → 900 × 600 = 540,000 samples (fast & compact!)
        nlat = int(round((lat1 - lat0) / step))
        nlon = int(round((lon1 - lon0) / step))
        grid = bytearray(nlat * nlon)  # 0 = no data / ocean

        used_files = []
        for t in meta["tiles"]:
            raw = zlib.decompress((self.raw_dir / t["bin"]).read_bytes())
            used_files.append(t["bin"])
            w, h, tw = t["w"], t["h"], t["tw"]
            t_lat0, t_lon0 = t["lat0"], t["lon0"]
            # GeoTIFF row 0 is top (lat1 = t_lat0 + 3), col 0 is left (t_lon0)
            r_start = max(0, int(math.floor((t_lat0 - lat0) / step)))
            r_end = min(nlat, int(math.ceil((t_lat0 + 3 - lat0) / step)))
            c_start = max(0, int(math.floor((t_lon0 - lon0) / step)))
            c_end = min(nlon, int(math.ceil((t_lon0 + 3 - lon0) / step)))
            for r in range(r_start, r_end):
                la = lat0 + (r + 0.5) * step
                if la < t_lat0 or la >= t_lat0 + 3:
                    continue
                py = min(h - 1, max(0, int((t_lat0 + 3 - la) / 3.0 * h)))
                row_off = py * tw
                out_row = r * nlon
                for c in range(c_start, c_end):
                    lo = lon0 + (c + 0.5) * step
                    if lo < t_lon0 or lo >= t_lon0 + 3:
                        continue
                    px = min(w - 1, max(0, int((lo - t_lon0) / 3.0 * w)))
                    idx = row_off + px
                    if idx < len(raw):
                        grid[out_row + c] = raw[idx]

        # Store as hex string / base64 for compact JSON interim (~120 KB compressed, or plain RLE)
        # Use simple run-length encoding [val, count, val, count, ...] for clean JSON!
        rle: list[int] = []
        if grid:
            cur = grid[0]
            cnt = 1
            for v in grid[1:]:
                if v == cur:
                    cnt += 1
                else:
                    rle.extend((cur, cnt))
                    cur, cnt = v, 1
            rle.extend((cur, cnt))

        return {
            "vintage": "ESA WorldCover 10m 2021 v200 (COG overview)",
            "lat0": lat0,
            "lon0": lon0,
            "step": step,
            "nlat": nlat,
            "nlon": nlon,
            "rle": rle,
            "_files": used_files,
        }


import math
