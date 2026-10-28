"""The repository's own inventory/: it passes its checks and comes from its script."""

import subprocess
import sys
import tomllib
from pathlib import Path

from classroom_runbooks import inventory, structure

ROOT = Path(__file__).resolve().parents[1]
CATEGORIES = [s.prefix for s in structure.load(ROOT / "structure.toml") if s.prefix]


def test_the_inventory_passes_its_checks_with_200_rooms_or_more() -> None:
    rooms = inventory.load(ROOT / "inventory", CATEGORIES).rooms
    assert len(rooms) >= 200


def test_every_room_type_and_runbook_category_is_used() -> None:
    inv = inventory.load(ROOT / "inventory", CATEGORIES)
    assert {r.profile for r in inv.rooms} == {p.id for p in inv.profiles}
    assert {e.category for e in inv.equipment} == set(CATEGORIES)


def test_the_script_writes_the_committed_rooms_csv(tmp_path: Path) -> None:
    out = tmp_path / "rooms.csv"
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "make_inventory.py"), "--out", str(out)],
        capture_output=True, text=True, check=False,
    )  # fmt: skip
    assert result.returncode == 0, result.stderr
    # Compared as text, since a Windows checkout may turn the committed file's LFs to CRLFs.
    committed = (ROOT / "inventory" / "rooms.csv").read_text(encoding="utf-8")
    assert out.read_text(encoding="utf-8") == committed
    assert b"\r" not in out.read_bytes()


def test_the_script_plans_every_building_and_only_those() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import make_inventory
    finally:
        sys.path.remove(str(ROOT / "scripts"))
    text = (ROOT / "inventory" / "buildings.toml").read_text(encoding="utf-8")
    codes = [b["code"] for b in tomllib.loads(text)["building"]]
    assert list(make_inventory.PLANS) == codes
    profiles = {p.id for p in inventory.load(ROOT / "inventory", CATEGORIES).profiles}
    assert set(make_inventory.EXTRAS) == set(make_inventory.WITHOUT) == profiles


def test_the_room_pages_are_the_ones_the_inventory_gives() -> None:
    sections = structure.load(ROOT / "structure.toml")
    rendered = inventory.pages(inventory.load(ROOT / "inventory", CATEGORIES), sections)
    assert inventory.check_pages(rendered, ROOT / "docs" / "rooms") == []
