"""Build sources.json: auto-generated Almanac bibliography with exact download URLs, dates, sizes & SHA-256."""

from __future__ import annotations

from ..core.fetch import read_manifest
from ..core.store import load_interim_meta, save_web
from ..sources import SOURCES

REQUIRES: list[str] = []
PRODUCES = ["sources.json"]
RUN_LAST = True


def build() -> None:
    out = []
    for src in SOURCES:
        manifest = read_manifest(src.id)
        meta = load_interim_meta(src.id)
        used = meta.get("files") or list(manifest.keys())
        files = []
        for rel in used:
            entry = manifest.get(rel)
            if not entry:
                continue
            files.append({
                "file": rel,
                "url": entry.get("url", ""),
                "retrieved": entry.get("retrieved", ""),
                "sha256": entry.get("sha256", ""),
                "bytes": entry.get("bytes", 0),
            })
        d = src.info.to_dict()
        d["vintage"] = meta.get("vintage") or ""
        d["files"] = files
        out.append(d)
    save_web("sources.json", out)
