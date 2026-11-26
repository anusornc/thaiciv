"""Validate web/data/*.json and print a data-quality report (PASS / NOTE / WARN / FAIL)."""

from __future__ import annotations

import json
from pathlib import Path

from .core.paths import WEB_DATA


def _load(web_dir: Path, name: str):
    p = web_dir / name
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def run_checks(web_dir: Path = WEB_DATA) -> tuple[list[tuple[str, str]], int]:
    lines: list[tuple[str, str]] = []
    fails = 0

    def report(level: str, msg: str):
        nonlocal fails
        if level == "FAIL":
            fails += 1
        lines.append((level, msg))

    world = _load(web_dir, "world.json")
    cities = _load(web_dir, "cities.json")
    states = _load(web_dir, "states.json")
    nation = _load(web_dir, "nation.json")
    lenses = _load(web_dir, "lenses.json")
    resources = _load(web_dir, "resources.json")
    counties = _load(web_dir, "counties.json")
    sources = _load(web_dir, "sources.json")

    for name, obj in [
        ("world.json", world),
        ("cities.json", cities),
        ("states.json", states),
        ("nation.json", nation),
        ("lenses.json", lenses),
        ("resources.json", resources),
        ("counties.json", counties),
        ("sources.json", sources),
    ]:
        if obj is None:
            report("FAIL", f"missing required file {name}")

    if world:
        g = world["grid"]
        n = g["cols"] * g["rows"]
        thai_cells = sum(1 for o in world["owner"] if o >= 0)
        water_cells = sum(1 for w in world["water"] if w > 0)
        n_states = len(world["states"])
        n_counties = len(world["counties"])
        if len(world["owner"]) != n or len(world["elev"]) != n or len(world["cover"]) != n:
            report("FAIL", f"world.json array length mismatch (expected {n})")
        else:
            report("PASS", f"world.json: {g['cols']}x{g['rows']} grid (R={g['radius']} km), {thai_cells} Thailand hexes, {water_cells} water, {n_states} provinces, {n_counties} districts, {len(world['rivers'])} rivers")
        if n_states != 77:
            report("FAIL", f"expected 77 provinces in world.json, got {n_states}")
        owned = {o for o in world["owner"] if o >= 0}
        if len(owned) != n_states:
            report("WARN", f"only {len(owned)}/{n_states} provinces own >= 1 hex")
        else:
            report("PASS", f"all {n_states} provinces own >= 1 hex")

    if cities and world:
        n = world["grid"]["cols"] * world["grid"]["rows"]
        bad = [c["id"] for c in cities if not (0 <= c["cell"] < n) or world["owner"][c["cell"]] < 0]
        if bad:
            report("FAIL", f"cities with invalid/non-Thailand cell: {bad[:5]}")
        else:
            caps = [c["name"] for c in cities if c.get("capital")]
            with_gdp = sum(1 for c in cities if c.get("gdp") is not None)
            with_inc = sum(1 for c in cities if c.get("median_income") is not None)
            report("PASS", f"cities.json: {len(cities)} provincial hubs, capital={caps}, {with_gdp} with GPP, {with_inc} with NSO income")

    if states and world:
        if len(states) != len(world["states"]):
            report("FAIL", f"states.json length {len(states)} != world.json states {len(world['states'])}")
        else:
            report("PASS", f"states.json: {len(states)} provinces aligned with world.json")

    if lenses and world:
        n = world["grid"]["cols"] * world["grid"]["rows"]
        bad_len = [l["id"] for l in lenses["lenses"] if len(l["values"]) != n]
        if bad_len:
            report("FAIL", f"lenses with wrong length: {bad_len}")
        else:
            report("PASS", f"lenses.json: {len(lenses['lenses'])} lenses across {len(lenses['groups'])} groups")

    if resources:
        report("PASS", f"resources.json: {len(resources['items'])} mapped sites across {len(resources['types'])} energy types")

    if counties:
        report("PASS", f"counties.json: {len(counties['rows'])} districts (amphoe) x {len(counties['columns'])} columns")

    for opt in ("districts.json", "citizens.json", "infrastructure.json", "wonders.json", "military.json", "trade.json", "disasters.json", "arsenic.json"):
        obj = _load(web_dir, opt)
        if obj is None:
            report("NOTE", f"optional file {opt} not present")
        else:
            report("PASS", f"{opt} loaded ({(web_dir / opt).stat().st_size / 1024:.1f} kB)")

    if sources:
        total_files = sum(len(s.get("files", [])) for s in sources)
        report("PASS", f"sources.json: {len(sources)} documented public sources ({total_files} checksummed files)")

    return lines, fails


def main() -> int:
    lines, fails = run_checks()
    for lvl, msg in lines:
        print(f"[{lvl:4}] {msg}")
    return 1 if fails else 0
