from pathlib import Path

import pytest

from classroom_runbooks.inventory import (
    GENERATED,
    Building,
    Equipment,
    InventoryError,
    Profile,
    Room,
    check_pages,
    load,
    main,
    pages,
    summary,
)
from classroom_runbooks.structure import parse

CATEGORIES = ("AV", "NET")
BUILDINGS = """
[[building]]
code = "ALD"
name = "Alder Hall"

[[building]]
code = "BIR"
name = "Birch Centre"
"""
EQUIPMENT = """
[[equipment]]
id = "projector"
name = "Projector"
category = "AV"
kind = "projector"

[[equipment]]
id = "speakers"
name = "Ceiling speakers"
category = "AV"
kind = "audio"

[[equipment]]
id = "wall-port"
name = "Wall network port"
category = "NET"
kind = "wired"

[[equipment]]
id = "webcam"
name = "Webcam"
category = "AV"
kind = "camera"
"""
PROFILES = """
[[profile]]
id = "standard"
name = "Standard classroom"
seats = [20, 60]
equipment = { wall-port = 2, projector = 1, speakers = 1 }
"""
STRUCTURE = """
[[section]]
path = "runbooks"
title = "Runbooks"
audience = ["technicians"]
purpose = "Faults."

[[section]]
path = "runbooks/av"
title = "Audio-visual"
audience = ["technicians"]
purpose = "AV."
prefix = "AV"

[[section]]
path = "runbooks/network"
title = "Network"
audience = ["technicians"]
purpose = "Network."
prefix = "NET"
"""
SECTIONS = parse(STRUCTURE)
ROOMS = """building,number,profile,seats,extra,without
ALD,101,standard,40,,
ALD,102,standard,24,webcam wall-port*2,speakers
BIR,201A,standard,60,,
"""


def write(folder: Path, **files: str) -> Path:
    contents = {
        "buildings.toml": BUILDINGS,
        "equipment.toml": EQUIPMENT,
        "profiles.toml": PROFILES,
        "rooms.csv": ROOMS,
    }
    for name, text in files.items():
        contents[name.replace("_", ".")] = text
    folder.mkdir(parents=True, exist_ok=True)
    for name, text in contents.items():
        if text is not None:
            (folder / name).write_bytes(text.encode("utf-8"))
    return folder


def problems(tmp_path: Path, **files: str) -> list[str]:
    with pytest.raises(InventoryError) as caught:
        load(write(tmp_path / "inventory", **files), CATEGORIES)
    assert str(caught.value) == "\n".join(caught.value.problems)
    return list(caught.value.problems)


def test_an_inventory_is_read_with_each_room_s_equipment_resolved(tmp_path: Path) -> None:
    inventory = load(write(tmp_path), CATEGORIES)
    assert inventory.buildings == (Building("ALD", "Alder Hall"), Building("BIR", "Birch Centre"))
    assert inventory.equipment[1] == Equipment("speakers", "Ceiling speakers", "AV", "audio")
    assert inventory.profiles == (
        Profile("standard", "Standard classroom", (20, 60),
                (("wall-port", 2), ("projector", 1), ("speakers", 1))),
    )  # fmt: skip
    first, second, third = inventory.rooms
    # In equipment.toml's order, not the profile's.
    assert first == Room(
        "ALD", "101", "standard", 40, (("projector", 1), ("speakers", 1), ("wall-port", 2))
    )
    assert first.id == "ALD-101"
    # An extra adds to what the type has; without removes it entirely.
    assert second.equipment == (("projector", 1), ("wall-port", 4), ("webcam", 1))
    assert third.id == "BIR-201A"
    assert inventory.building("BIR").name == "Birch Centre"
    assert inventory.item("webcam").category == "AV"
    assert inventory.profile("standard").seats == (20, 60)
    with pytest.raises(KeyError):
        inventory.item("nothing")


def test_a_crlf_inventory_reads_the_same(tmp_path: Path) -> None:
    lf = load(write(tmp_path / "lf"), CATEGORIES)
    files = {
        "buildings_toml": BUILDINGS,
        "equipment_toml": EQUIPMENT,
        "profiles_toml": PROFILES,
        "rooms_csv": ROOMS,
    }
    crlf = {k: v.replace("\n", "\r\n") for k, v in files.items()}
    assert load(write(tmp_path / "crlf", **crlf), CATEGORIES) == lf


def test_the_summary_counts_rooms_seats_types_and_equipment(tmp_path: Path) -> None:
    assert summary(load(write(tmp_path), CATEGORIES)) == [
        "2 buildings, 3 rooms, 124 seats",
        "  Standard classroom: 3 rooms",
        "14 pieces of equipment: AV 6, NET 8",
    ]


@pytest.mark.parametrize(
    ("rows", "expected"),
    [
        ("ALD,103,standard,40,,\nALD,103,standard,30,,\n",
         "rooms.csv line 6: ALD-103 is already on line 5"),
        ("XYZ,101,standard,40,,\n", "line 5: building 'XYZ' is not in buildings.toml"),
        ("ALD,10,standard,40,,\n", "line 5: a room number is 3 or 4 digits and an optional "
                                   "capital, not '10'"),
        ("ALD,101b,standard,40,,\n", "not '101b'"),
        ("ALD,105,lab,40,,\n", "line 5: room type 'lab' is not in profiles.toml"),
        ("ALD,105,standard,forty,,\n", "line 5: seats is a whole number from 1, not 'forty'"),
        ("ALD,105,standard,0,,\n", "not '0'"),
        ("ALD,105,standard,-4,,\n", "not '-4'"),
        ("ALD,105,standard,61,,\n", "line 5: 61 seats is outside Standard classroom's 20 to 60"),
        ("ALD,105,standard,19,,\n", "19 seats is outside"),
        ("ALD,105,standard,40,laser,\n", "line 5: an extra is a known equipment id with an "
                                         "optional *count from 1 to 99, not 'laser'"),
        ("ALD,105,standard,40,webcam*0,\n", "not 'webcam*0'"),
        ("ALD,105,standard,40,webcam*100,\n", "not 'webcam*100'"),
        ("ALD,105,standard,40,webcam*,\n", "not 'webcam*'"),
        ("ALD,105,standard,40,webcam webcam*2,\n", "line 5: extra webcam is listed twice"),
        ("ALD,105,standard,40,,webcam\n",
         "line 5: without 'webcam', which Standard classroom does not have"),
        ("ALD,105,standard,40,,speakers speakers\n", "line 5: an item is listed twice in without"),
        ("ALD,105,standard,40,speakers,speakers\n", "line 5: speakers is both extra and without"),
        ("ALD,105,standard,40,,projector speakers wall-port\n",
         "line 5: the room is left with no equipment"),
        ("ALD,105 ,standard,40,,\n", "line 5: number has spaces at an end"),
        ("ALD,105,standard,40,\n", "line 5 has 5 values, not 6"),
        ("ALD,105,standard,40,,,\n", "line 5 has 7 values, not 6"),
        ("\nALD,105,standard,40,,\n", "line 5 is blank"),
    ],
)  # fmt: skip
def test_a_room_row_that_breaks_a_rule_is_named_with_its_line(
    tmp_path: Path, rows: str, expected: str
) -> None:
    found = problems(tmp_path, rooms_csv=ROOMS + rows)
    assert len(found) == 1, found
    assert expected in found[0], found


def test_every_bad_row_is_reported_not_only_the_first(tmp_path: Path) -> None:
    found = problems(tmp_path, rooms_csv=ROOMS + "XYZ,101,standard,40,,\nALD,1,lab,0,,\n")
    assert [p.split(": ", 1)[0][-6:] for p in found] == ["line 5", "line 6", "line 6", "line 6"]


def test_a_row_is_named_by_the_line_it_starts_on(tmp_path: Path) -> None:
    # A quoted value spanning lines 5 and 6 (the extras may be on separate lines).
    rows = ROOMS + 'ALD,105,standard,40,"webcam\nspeakers",\nALD,106,lab,40,,\nALD,107,lab,40,,\n'
    rooms = tmp_path / "inventory" / "rooms.csv"
    assert problems(tmp_path, rooms_csv=rows) == [
        f"{rooms} line 7: room type 'lab' is not in profiles.toml",
        f"{rooms} line 8: room type 'lab' is not in profiles.toml",
    ]
    spanning = ROOMS + 'ALD,105,standard,40,"webcam\nspeakers",\n'
    room = load(write(tmp_path / "ok", rooms_csv=spanning), CATEGORIES).rooms[-1]
    assert room.equipment == (("projector", 1), ("speakers", 2), ("wall-port", 2), ("webcam", 1))


def test_a_damaged_csv_is_reported(tmp_path: Path) -> None:
    rooms = tmp_path / "inventory" / "rooms.csv"
    assert problems(tmp_path, rooms_csv="room,profile\nALD-101,standard\n") == [
        f"{rooms}: the first line must be the columns building,number,profile,seats,extra,without"
    ]
    assert problems(tmp_path, rooms_csv="")[0].endswith("the first line must be the columns "
                                                        "building,number,profile,seats,extra,"
                                                        "without")  # fmt: skip
    assert "the first line must be" in problems(tmp_path, rooms_csv="﻿" + ROOMS)[0]
    # An unclosed quote is not read as a value running to the end of the file.
    assert problems(tmp_path, rooms_csv=ROOMS + 'ALD,"105\nALD,106,standard,40,,\n') == [
        f"{rooms} line 5: not CSV: unexpected end of data"
    ]


@pytest.mark.parametrize(
    ("name", "text", "expected"),
    [
        ("buildings_toml", 'code = "ALD"', "unknown keys code; entries are [[building]]"),
        ("buildings_toml", "[[building]]\ncode = 'ALD'\n", "building 1: missing name"),
        ("buildings_toml", "[[building]]\ncode = 'ALD'\nname = 'A'\nfloors = 3\n",
         "building 1: unknown keys floors"),
        ("buildings_toml", "[[building]]\ncode = 'ald'\nname = 'A'\n",
         "a code is 2 to 4 capital letters, not 'ald'"),
        ("buildings_toml", "[[building]]\ncode = 'ALD'\nname = ' A'\n",
         "building ALD: a name is one line of text without spaces at its ends or a '|': ' A'"),
        # A name is a page's heading and a table cell, so one line without a '|'.
        ("buildings_toml", BUILDINGS.replace('"Alder Hall"', '"Alder\\nHall"'),
         "building ALD: a name is one line"),
        ("buildings_toml", BUILDINGS.replace('"Alder Hall"', '"Alder | Hall"'),
         "building ALD: a name is one line"),
        ("buildings_toml", BUILDINGS.replace('"Alder Hall"', '"Alder\\u2028Hall"'),
         "building ALD: a name is one line"),
        # "$" alone would also match before a final newline.
        ("buildings_toml", BUILDINGS.replace('"ALD"', '"ALD\\n"'),
         "a code is 2 to 4 capital letters, not 'ALD\\n'"),
        ("equipment_toml", EQUIPMENT.replace('"webcam"', '"webcam\\n"', 1),
         "an id is lower-case words joined by hyphens, not 'webcam\\n'"),
        ("equipment_toml", EQUIPMENT.replace('"camera"', '"camera\\n"'),
         "equipment webcam: kind is lower-case words"),
        ("equipment_toml", EQUIPMENT.replace('"Webcam"', '"Web|cam"'),
         "equipment webcam: a name is one line"),
        ("profiles_toml", PROFILES.replace('"standard"', '"standard\\n"'),
         "an id is lower-case words joined by hyphens, not 'standard\\n'"),
        ("profiles_toml", PROFILES.replace('"Standard classroom"', '"Standard\\tclassroom"'),
         "profile standard: a name is one line"),
        ("buildings_toml", BUILDINGS + "[[building]]\ncode = 'ALD'\nname = 'Other'\n",
         "the code ALD is used more than once"),
        ("buildings_toml", "building = 3\n", "no [[building]] entries"),
        ("buildings_toml", "building = [3]\n", "building 1 is not a table of keys"),
        ("buildings_toml", "[[building\n", "not TOML"),
        ("equipment_toml", EQUIPMENT.replace('"wall-port"', '"Wall_Port"', 1),
         "an id is lower-case words joined by hyphens, not 'Wall_Port'"),
        ("equipment_toml", EQUIPMENT.replace('"NET"', '"PER"'),
         "equipment wall-port: category 'PER' is not a runbook category (AV, NET)"),
        ("equipment_toml", EQUIPMENT.replace('"NET"', '["NET"]'),
         "category ['NET'] is not a runbook category"),
        ("equipment_toml", EQUIPMENT.replace('"wired"', '"Wired Port"'),
         "equipment wall-port: kind is lower-case words"),
        ("equipment_toml", EQUIPMENT.replace('"Webcam"', '"Projector"'),
         "the name Projector is used more than once"),
        ("profiles_toml", PROFILES.replace("[20, 60]", "[60, 20]"),
         "profile standard: seats is [fewest, most], whole numbers from 1: [60, 20]"),
        ("profiles_toml", PROFILES.replace("[20, 60]", "[0, 20]"), "seats is [fewest, most]"),
        ("profiles_toml", PROFILES.replace("[20, 60]", "[20.0, 60]"), "seats is [fewest, most]"),
        ("profiles_toml", PROFILES.replace("[20, 60]", "[20]"), "seats is [fewest, most]"),
        ("profiles_toml", PROFILES.replace("projector = 1", "laser = 1"),
         "each equipment entry is a known id and a count from 1 to 99, not laser = 1"),
        ("profiles_toml", PROFILES.replace("projector = 1", "projector = 0"), "not projector = 0"),
        ("profiles_toml", PROFILES.replace("projector = 1", "projector = true"),
         "not projector = True"),
        ("profiles_toml", PROFILES.replace("projector = 1", "projector = 100"),
         "not projector = 100"),
        ("profiles_toml", PROFILES.replace("{ wall-port = 2, projector = 1, speakers = 1 }", "{}"),
         "equipment is a table of equipment ids and counts"),
    ],
)  # fmt: skip
def test_a_toml_file_that_breaks_a_rule_is_reported(
    tmp_path: Path, name: str, text: str, expected: str
) -> None:
    found = problems(tmp_path, **{name: text})
    assert any(expected in p for p in found), found


def test_a_building_with_no_rooms_and_equipment_no_room_has_are_reported(tmp_path: Path) -> None:
    extra = BUILDINGS + "[[building]]\ncode = 'CED'\nname = 'Cedar Library'\n"
    assert problems(tmp_path, buildings_toml=extra) == [
        f"{tmp_path / 'inventory' / 'rooms.csv'}: no rooms in CED"
    ]
    rooms = ROOMS.replace("webcam ", "")
    assert problems(tmp_path / "2", rooms_csv=rooms) == [
        f"{tmp_path / '2' / 'inventory' / 'equipment.toml'}: no room has webcam"
    ]


def test_unreadable_files_are_reported_together(tmp_path: Path) -> None:
    folder = write(tmp_path / "inventory")
    (folder / "buildings.toml").unlink()
    (folder / "profiles.toml").write_bytes(b"\xff\xfe[[profile]]")
    (folder / "rooms.csv").unlink()
    (folder / "rooms.csv").mkdir()
    with pytest.raises(InventoryError) as caught:
        load(folder, CATEGORIES)
    assert caught.value.problems == (
        f"{folder / 'buildings.toml'} is missing",
        f"{folder / 'profiles.toml'} is not UTF-8 text",
        f"{folder / 'rooms.csv'} is a folder, not a file",
    )
    with pytest.raises(InventoryError, match="is not a folder"):
        load(tmp_path / "nowhere", CATEGORIES)


def test_the_command_prints_the_summary_or_every_problem(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    structure = tmp_path / "structure.toml"
    structure.write_text(STRUCTURE, encoding="utf-8")
    folder = write(tmp_path / "inventory")
    args = ["--inventory", str(folder), "--structure", str(structure)]
    assert main(args) == 0
    assert capsys.readouterr().out.splitlines()[0] == "2 buildings, 3 rooms, 124 seats"
    write(folder, rooms_csv=ROOMS + "XYZ,1,standard,40,,\n")
    assert main(args) == 1
    out, err = capsys.readouterr()
    assert out == "2 problems\n"
    assert err.count("problem: ") == 2
    assert main(["--inventory", str(folder), "--structure", str(tmp_path / "none.toml")]) == 1
    assert "error: " in capsys.readouterr().err


def test_the_pages_are_an_index_and_one_page_per_building(tmp_path: Path) -> None:
    rendered = pages(load(write(tmp_path), CATEGORIES), SECTIONS)
    assert list(rendered) == ["index.md", "ald.md", "bir.md"]
    index = rendered["index.md"].splitlines()
    assert index[:3] == ["# Rooms", "", GENERATED]
    assert "3 rooms in 2 buildings, 124 seats." in index
    assert "| [Alder Hall](ald.md) | ALD | 2 | 64 |" in index
    assert ("| Standard classroom | 3 | 20–60 | Projector, Ceiling speakers, "
            "Wall network port ×2 |") in index  # fmt: skip
    assert "| Webcam | [Audio-visual](../runbooks/av/index.md) | 1 | 1 |" in index
    assert "| Wall network port | [Network](../runbooks/network/index.md) | 3 | 8 |" in index
    assert rendered["ald.md"] == "\n".join([
        "# Alder Hall (ALD)", "", GENERATED, "",
        "2 rooms, 64 seats. [All buildings](index.md)", "",
        "| Room | Type | Seats |", "| --- | --- | ---: |",
        "| [ALD-101](#ald-101) | Standard classroom | 40 |",
        "| [ALD-102](#ald-102) | Standard classroom | 24 |", "",
        "## ALD-101", "", "Standard classroom, 40 seats.", "",
        "- **Audio-visual** ([runbooks](../runbooks/av/index.md)): Projector, Ceiling speakers",
        "- **Network** ([runbooks](../runbooks/network/index.md)): Wall network port ×2", "",
        "## ALD-102", "",
        "Standard classroom, 24 seats. Unlike its type: also Wall network port ×2, Webcam; "
        "no Ceiling speakers.", "",
        "- **Audio-visual** ([runbooks](../runbooks/av/index.md)): Projector, Webcam",
        "- **Network** ([runbooks](../runbooks/network/index.md)): Wall network port ×4", "",
    ])  # fmt: skip


def test_pages_are_checked_against_the_inventory(tmp_path: Path) -> None:
    rendered = pages(load(write(tmp_path / "inventory"), CATEGORIES), SECTIONS)
    rooms = tmp_path / "rooms"
    rooms.mkdir()
    assert check_pages(rendered, rooms) == [f"{rooms / n} is missing" for n in rendered]
    for name, text in rendered.items():
        # A Windows checkout's CRLFs are the same page.
        (rooms / name).write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
    assert check_pages(rendered, rooms) == []
    (rooms / "ald.md").write_text(rendered["ald.md"].replace("40 seats", "41 seats"), "utf-8")
    (rooms / "ced.md").write_text("# Cedar Hall\n", encoding="utf-8")
    (rooms / "notes.txt").write_text("not a page\n", encoding="utf-8")
    assert check_pages(rendered, rooms) == [
        f"{rooms / 'ald.md'} is not the page the inventory gives",
        f"{rooms / 'ced.md'} is not a page the inventory gives",
    ]


def test_the_command_writes_and_checks_the_pages(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    structure = tmp_path / "structure.toml"
    structure.write_text(STRUCTURE, encoding="utf-8")
    rooms = tmp_path / "rooms"
    rooms.mkdir()
    args = ["--inventory", str(write(tmp_path / "inventory")), "--structure", str(structure),
            "--rooms", str(rooms)]  # fmt: skip
    assert main([*args, "--check"]) == 1
    assert capsys.readouterr().out.endswith("3 problems; `--write` writes them\n")
    assert main([*args, "--write"]) == 0
    assert capsys.readouterr().out.endswith(
        f"wrote 3 pages to {rooms}\n3 room pages match the inventory\n"
    )
    assert sorted(p.name for p in rooms.iterdir()) == ["ald.md", "bir.md", "index.md"]
    assert b"\r" not in (rooms / "ald.md").read_bytes()
    assert main([*args, "--check"]) == 0
    (rooms / "old.md").write_text("# Old Hall\n", encoding="utf-8")
    assert main([*args, "--write"]) == 1
    out, err = capsys.readouterr()
    assert out.endswith("1 problems; remove the pages it does not give\n")
    assert f"problem: {rooms / 'old.md'} is not a page the inventory gives" in err
    assert main([*args[:4], "--rooms", str(tmp_path / "none"), "--write"]) == 1
    assert "is not a folder" in capsys.readouterr().err
    with pytest.raises(SystemExit):
        main([*args, "--write", "--check"])


def test_an_entry_reported_where_it_is_defined_is_not_reported_again_where_used(
    tmp_path: Path,
) -> None:
    # 3 rooms of a type whose seats are wrong: one problem, not one more per room.
    assert problems(tmp_path / "a", profiles_toml=PROFILES.replace("[20, 60]", "[60, 20]")) == [
        f"{tmp_path / 'a' / 'inventory' / 'profiles.toml'}: profile standard: seats is "
        "[fewest, most], whole numbers from 1: [60, 20]"
    ]
    # Equipment a room type and every room have, or one room's extra.
    for i, (old, new) in enumerate([('"Projector"', '" Projector"'), ('"camera"', '"Camera"')]):
        found = problems(tmp_path / str(i), equipment_toml=EQUIPMENT.replace(old, new))
        assert len(found) == 1 and "equipment.toml: equipment " in found[0], found
    found = problems(tmp_path / "b", buildings_toml=BUILDINGS.replace('"Alder Hall"', '""'))
    assert found == [
        f"{tmp_path / 'b' / 'inventory' / 'buildings.toml'}: building ALD: "
        "a name is one line of text without spaces at its ends or a '|': ''"
    ]
    # A row's other problems are still reported.
    rows = ROOMS + "ALD,10,standard,40,,\n"
    found = problems(tmp_path / "c", buildings_toml=BUILDINGS.replace('"Alder Hall"', '""'),
                     rooms_csv=rows)  # fmt: skip
    assert len(found) == 2 and "line 5: a room number is 3 or 4 digits" in found[1], found
    # Unknown names are still unknown.
    found = problems(tmp_path / "d", profiles_toml=PROFILES.replace("[20, 60]", "[60, 20]"),
                     rooms_csv=ROOMS + "ALD,105,lab,40,,\n")  # fmt: skip
    assert len(found) == 2 and "line 5: room type 'lab' is not in profiles.toml" in found[1]


def test_a_room_type_no_room_is_of_is_reported_with_equipment_only_it_lists(
    tmp_path: Path,
) -> None:
    studio = (
        '\n[[profile]]\nid = "studio"\nname = "Studio"\nseats = [5, 9]\n'
        "equipment = { webcam = 1 }\n"
    )
    # Webcam is then in a type, but in no room.
    rooms = ROOMS.replace("webcam ", "")
    folder = tmp_path / "inventory"
    assert problems(tmp_path, profiles_toml=PROFILES + studio, rooms_csv=rooms) == [
        f"{folder / 'rooms.csv'}: no room is of type studio",
        f"{folder / 'equipment.toml'}: no room has webcam",
    ]


def test_unreadable_pages_are_reported_and_unwritable_ones_stop_the_command(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    rendered = pages(load(write(tmp_path / "inventory"), CATEGORIES), SECTIONS)
    rooms = tmp_path / "rooms"
    rooms.mkdir()
    for name, text in rendered.items():
        (rooms / name).write_text(text, encoding="utf-8", newline="\n")
    (rooms / "ald.md").write_bytes(b"\xff\xfe")
    assert check_pages(rendered, rooms) == [f"{rooms / 'ald.md'} is not UTF-8 text"]
    (rooms / "ald.md").unlink()
    (rooms / "ald.md").mkdir()  # a folder where a page goes
    structure = tmp_path / "structure.toml"
    structure.write_text(STRUCTURE, encoding="utf-8")
    args = ["--inventory", str(tmp_path / "inventory"), "--structure", str(structure),
            "--rooms", str(rooms), "--write"]  # fmt: skip
    assert main(args) == 1
    assert f"error: {rooms / 'ald.md'} cannot be written: " in capsys.readouterr().err
