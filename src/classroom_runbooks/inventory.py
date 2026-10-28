"""The room inventory: buildings, equipment, room types and rooms, read and checked.

The inventory is data, kept in ``inventory/`` at the repository's root:

- ``buildings.toml``: each building's code (2 to 4 capital letters) and name;
- ``equipment.toml``: each kind of equipment a room can have, with the runbook category
  (a prefix in ``structure.toml``, such as ``AV``) whose runbooks cover it;
- ``profiles.toml``: each room type, the seats a room of that type has, and the
  equipment it is fitted with, by count;
- ``rooms.csv``: one row per room: its building, number, type and seats, and how it
  differs from its type: equipment ``extra`` (``webcam`` or ``wall-port*2``) and
  equipment it is ``without``.

A room's identifier is its building's code and its number: ``ALD-104``.

``python -m classroom_runbooks.inventory`` reads and checks it all and prints a
summary; every problem found is listed, with the file and line, and the exit code is 1.
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import sys
import tomllib
from collections import Counter
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from pathlib import Path

from classroom_runbooks import structure

DEFAULT_INVENTORY = Path("inventory")
ROOM_COLUMNS = ("building", "number", "profile", "seats", "extra", "without")
MAX_COUNT = 99
"""The most of one kind of equipment a room type or a room's extras can list."""
_CODE = re.compile(r"^[A-Z]{2,4}$")
_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_NUMBER = re.compile(r"^[0-9]{3,4}[A-Z]?$")
_EXTRA = re.compile(r"^([a-z0-9]+(?:-[a-z0-9]+)*)(?:\*([0-9]+))?$")


class InventoryError(ValueError):
    """The inventory cannot be read, or breaks a rule; ``problems`` lists each one."""

    def __init__(self, problems: Sequence[str]) -> None:
        self.problems = tuple(problems)
        super().__init__("\n".join(self.problems))


@dataclass(frozen=True)
class Building:
    code: str
    name: str


@dataclass(frozen=True)
class Equipment:
    id: str
    name: str
    category: str
    """The prefix of the runbook category whose runbooks cover it."""
    kind: str
    """What it is within its category (``projector``, ``audio``), for grouping."""


@dataclass(frozen=True)
class Profile:
    id: str
    name: str
    seats: tuple[int, int]
    """The fewest and most seats a room of this type has."""
    equipment: tuple[tuple[str, int], ...]
    """Each equipment id it is fitted with and how many, in the order written."""


@dataclass(frozen=True)
class Room:
    building: str
    number: str
    profile: str
    seats: int
    equipment: tuple[tuple[str, int], ...]
    """The equipment in the room, its type's with the room's differences applied,
    in ``equipment.toml``'s order."""

    @property
    def id(self) -> str:
        return f"{self.building}-{self.number}"


@dataclass(frozen=True)
class Inventory:
    buildings: tuple[Building, ...]
    equipment: tuple[Equipment, ...]
    profiles: tuple[Profile, ...]
    rooms: tuple[Room, ...]

    def building(self, code: str) -> Building:
        return _find(self.buildings, "code", code)

    def item(self, equipment_id: str) -> Equipment:
        return _find(self.equipment, "id", equipment_id)

    def profile(self, profile_id: str) -> Profile:
        return _find(self.profiles, "id", profile_id)


def _find(entries, key, value):
    for entry in entries:
        if getattr(entry, key) == value:
            return entry
    raise KeyError(value)


def _read(path: Path, problems: list[str]) -> str | None:
    if path.is_dir():
        problems.append(f"{path} is a folder, not a file")
        return None
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        problems.append(f"{path} is missing")
    except UnicodeDecodeError:
        problems.append(f"{path} is not UTF-8 text")
    except OSError as exc:
        problems.append(f"{path} cannot be read: {exc.strerror or exc}")
    return None


def _entries(path: Path, key: str, fields: set[str], problems: list[str]) -> list[dict]:
    """The ``[[key]]`` tables of a TOML file, each with only ``fields``; [] on a problem."""
    text = _read(path, problems)
    if text is None:
        return []
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        problems.append(f"{path}: not TOML: {exc}")
        return []
    unknown = sorted(set(data) - {key})
    if unknown:
        problems.append(f"{path}: unknown keys {', '.join(unknown)}; entries are [[{key}]]")
    entries = data.get(key)
    if not isinstance(entries, list) or not entries:
        problems.append(f"{path}: no [[{key}]] entries")
        return []
    good = []
    for i, entry in enumerate(entries, 1):
        if not isinstance(entry, dict):
            problems.append(f"{path}: {key} {i} is not a table of keys")
            continue
        missing = sorted(fields - set(entry))
        extra = sorted(set(entry) - fields)
        if missing or extra:
            said = [f"missing {', '.join(missing)}"] * bool(missing)
            said += [f"unknown keys {', '.join(extra)}"] * bool(extra)
            problems.append(f"{path}: {key} {i}: {'; '.join(said)}")
            continue
        good.append(entry)
    return good


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value == value.strip()


def _count(value: object) -> bool:
    return type(value) is int and 1 <= value <= MAX_COUNT


def _unique(path: Path, name: str, values: list[str], problems: list[str]) -> None:
    repeated = sorted(v for v, n in Counter(values).items() if n > 1)
    if repeated:
        problems.append(f"{path}: the {name} {', '.join(repeated)} is used more than once")


def _buildings(path: Path, problems: list[str]) -> list[Building]:
    buildings = []
    for i, entry in enumerate(_entries(path, "building", {"code", "name"}, problems), 1):
        code, name = entry["code"], entry["name"]
        if not isinstance(code, str) or not _CODE.match(code):
            problems.append(f"{path}: building {i}: a code is 2 to 4 capital letters, not {code!r}")
        elif not _text(name):
            problems.append(f"{path}: building {code}: name must be text without end spaces")
        else:
            buildings.append(Building(code, name))
    _unique(path, "code", [b.code for b in buildings], problems)
    _unique(path, "name", [b.name for b in buildings], problems)
    return buildings


def _equipment(path: Path, categories: Collection[str], problems: list[str]) -> list[Equipment]:
    fields = {"id", "name", "category", "kind"}
    items = []
    for i, entry in enumerate(_entries(path, "equipment", fields, problems), 1):
        item_id = entry["id"]
        if not isinstance(item_id, str) or not _SLUG.match(item_id):
            problems.append(
                f"{path}: equipment {i}: an id is lower-case words joined by hyphens, "
                f"not {item_id!r}"
            )
            continue
        where = f"{path}: equipment {item_id}"
        if not _text(entry["name"]):
            problems.append(f"{where}: name must be text without end spaces")
        elif not isinstance(entry["category"], str) or entry["category"] not in categories:
            problems.append(
                f"{where}: category {entry['category']!r} is not a runbook category "
                f"({', '.join(categories)})"
            )
        elif not isinstance(entry["kind"], str) or not _SLUG.match(entry["kind"]):
            problems.append(f"{where}: kind is lower-case words joined by hyphens")
        else:
            items.append(Equipment(item_id, entry["name"], entry["category"], entry["kind"]))
    _unique(path, "id", [e.id for e in items], problems)
    _unique(path, "name", [e.name for e in items], problems)
    return items


def _profiles(path: Path, known: Collection[str], problems: list[str]) -> list[Profile]:
    fields = {"id", "name", "seats", "equipment"}
    profiles = []
    for i, entry in enumerate(_entries(path, "profile", fields, problems), 1):
        profile_id = entry["id"]
        if not isinstance(profile_id, str) or not _SLUG.match(profile_id):
            problems.append(
                f"{path}: profile {i}: an id is lower-case words joined by hyphens, "
                f"not {profile_id!r}"
            )
            continue
        where = f"{path}: profile {profile_id}"
        seats, fitted = entry["seats"], entry["equipment"]
        if not _text(entry["name"]):
            problems.append(f"{where}: name must be text without end spaces")
            continue
        if not (
            isinstance(seats, list)
            and len(seats) == 2
            and all(type(s) is int for s in seats)
            and 1 <= seats[0] <= seats[1]
        ):
            problems.append(f"{where}: seats is [fewest, most], whole numbers from 1: {seats!r}")
            continue
        if not isinstance(fitted, dict) or not fitted:
            problems.append(f"{where}: equipment is a table of equipment ids and counts")
            continue
        bad = [f"{k} = {v!r}" for k, v in fitted.items() if k not in known or not _count(v)]
        if bad:
            problems.append(
                f"{where}: each equipment entry is a known id and a count from 1 to "
                f"{MAX_COUNT}, not {', '.join(bad)}"
            )
            continue
        profiles.append(Profile(profile_id, entry["name"], (seats[0], seats[1]),
                                tuple(fitted.items())))  # fmt: skip
    _unique(path, "id", [p.id for p in profiles], problems)
    _unique(path, "name", [p.name for p in profiles], problems)
    return profiles


def _rooms(
    path: Path,
    buildings: Collection[str],
    equipment: Sequence[str],
    profiles: dict[str, Profile],
    problems: list[str],
) -> list[Room]:
    text = _read(path, problems)
    if text is None:
        return []
    # Strict, so an unclosed quote is an error, not a value running to the end of the file.
    reader = csv.reader(io.StringIO(text), strict=True)
    rows: list[tuple[int, list[str]]] = []  # each row with the line it starts on
    start = 1
    try:
        for row in reader:
            rows.append((start, row))
            start = reader.line_num + 1
    except csv.Error as exc:
        problems.append(f"{path} line {start}: not CSV: {exc}")
        return []
    if not rows or tuple(rows[0][1]) != ROOM_COLUMNS:
        problems.append(f"{path}: the first line must be the columns {','.join(ROOM_COLUMNS)}")
        return []
    rooms, lines = [], {}
    for line, row in rows[1:]:
        where = f"{path} line {line}"
        if not row:
            problems.append(f"{where} is blank")
            continue
        if len(row) != len(ROOM_COLUMNS):
            problems.append(f"{where} has {len(row)} values, not {len(ROOM_COLUMNS)}")
            continue
        room = _room(where, dict(zip(ROOM_COLUMNS, row, strict=True)), buildings, equipment,
                     profiles, problems)  # fmt: skip
        if room is None:
            continue
        if room.id in lines:
            problems.append(f"{where}: {room.id} is already on line {lines[room.id]}")
            continue
        lines[room.id] = line
        rooms.append(room)
    return rooms


def _room(
    where: str,
    values: dict[str, str],
    buildings: Collection[str],
    equipment: Sequence[str],
    profiles: dict[str, Profile],
    problems: list[str],
) -> Room | None:
    spaced = [k for k, v in values.items() if v != v.strip()]
    if spaced:
        problems.append(f"{where}: {', '.join(spaced)} has spaces at an end")
        return None
    building, number, profile_id = values["building"], values["number"], values["profile"]
    said = len(problems)
    if building not in buildings:
        problems.append(f"{where}: building {building!r} is not in buildings.toml")
    if not _NUMBER.match(number):
        problems.append(
            f"{where}: a room number is 3 or 4 digits and an optional capital, not {number!r}"
        )
    profile = profiles.get(profile_id)
    if profile is None:
        problems.append(f"{where}: room type {profile_id!r} is not in profiles.toml")
    seats = int(values["seats"]) if re.fullmatch(r"[1-9][0-9]*", values["seats"]) else None
    if seats is None:
        problems.append(f"{where}: seats is a whole number from 1, not {values['seats']!r}")
    elif profile is not None and not profile.seats[0] <= seats <= profile.seats[1]:
        low, high = profile.seats
        problems.append(f"{where}: {seats} seats is outside {profile.name}'s {low} to {high}")
    extra: dict[str, int] = {}
    for word in values["extra"].split():
        match = _EXTRA.match(word)
        count = int(match.group(2) or 1) if match else 0
        if not match or match.group(1) not in equipment or not 1 <= count <= MAX_COUNT:
            problems.append(
                f"{where}: an extra is a known equipment id with an optional *count "
                f"from 1 to {MAX_COUNT}, not {word!r}"
            )
        elif match.group(1) in extra:
            problems.append(f"{where}: extra {match.group(1)} is listed twice")
        else:
            extra[match.group(1)] = count
    without = values["without"].split()
    fitted = dict(profile.equipment) if profile is not None else {}
    for item in without:
        if profile is not None and item not in fitted:
            problems.append(f"{where}: without {item!r}, which {profile.name} does not have")
        if item in extra:
            problems.append(f"{where}: {item} is both extra and without")
    if len(set(without)) != len(without):
        problems.append(f"{where}: an item is listed twice in without")
    if len(problems) > said or profile is None or seats is None:
        return None
    for item in without:
        del fitted[item]
    for item, count in extra.items():
        fitted[item] = fitted.get(item, 0) + count
    if not fitted:
        problems.append(f"{where}: the room is left with no equipment")
        return None
    ordered = tuple(sorted(fitted.items(), key=lambda pair: equipment.index(pair[0])))
    return Room(building, number, profile_id, seats, ordered)


def load(folder: Path, categories: Collection[str]) -> Inventory:
    """The inventory in ``folder``, checked; ``categories`` are the runbook prefixes."""
    folder = Path(folder)
    if not folder.is_dir():
        raise InventoryError([f"{folder} is not a folder"])
    problems: list[str] = []
    buildings = _buildings(folder / "buildings.toml", problems)
    equipment = _equipment(folder / "equipment.toml", categories, problems)
    profiles = _profiles(folder / "profiles.toml", {e.id for e in equipment}, problems)
    rooms = _rooms(folder / "rooms.csv", {b.code for b in buildings},
                   [e.id for e in equipment], {p.id: p for p in profiles}, problems)  # fmt: skip
    if not problems:
        empty = [b.code for b in buildings if not any(r.building == b.code for r in rooms)]
        if empty:
            problems.append(f"{folder / 'rooms.csv'}: no rooms in {', '.join(empty)}")
        unused = [e.id for e in equipment if not any(e.id in dict(p.equipment) for p in profiles)
                  and not any(e.id in dict(r.equipment) for r in rooms)]  # fmt: skip
        if unused:
            problems.append(f"{folder / 'equipment.toml'}: no room has {', '.join(unused)}")
    if problems:
        raise InventoryError(problems)
    return Inventory(tuple(buildings), tuple(equipment), tuple(profiles), tuple(rooms))


def summary(inventory: Inventory) -> list[str]:
    """Counts of buildings, rooms, seats, room types and equipment, one per line."""
    rooms = inventory.rooms
    lines = [
        f"{len(inventory.buildings)} buildings, {len(rooms)} rooms, "
        f"{sum(r.seats for r in rooms):,} seats"
    ]
    by_profile = Counter(r.profile for r in rooms)
    for p in inventory.profiles:
        lines.append(f"  {p.name}: {by_profile[p.id]} rooms")
    devices: Counter[str] = Counter()
    for room in rooms:
        for item, count in room.equipment:
            devices[inventory.item(item).category] += count
    categories = dict.fromkeys(e.category for e in inventory.equipment)
    lines.append(
        f"{sum(devices.values()):,} pieces of equipment: "
        + ", ".join(f"{c} {devices[c]:,}" for c in categories)
    )
    return lines


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m classroom_runbooks.inventory",
        description="Check the room inventory and print a summary of it",
    )
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--structure", type=Path, default=structure.DEFAULT_STRUCTURE)
    args = parser.parse_args(argv)
    try:
        sections = structure.load(args.structure)
        inventory = load(args.inventory, [s.prefix for s in sections if s.prefix])
    except structure.StructureError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except InventoryError as exc:
        for problem in exc.problems:
            print(f"problem: {problem}", file=sys.stderr)
        print(f"{len(exc.problems)} problems")
        return 1
    print("\n".join(summary(inventory)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
