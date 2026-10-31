from pathlib import Path

import pytest

from classroom_runbooks import runbook, validate
from classroom_runbooks.inventory import Building, Equipment, Inventory, Room
from classroom_runbooks.structure import Section

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = runbook.read(ROOT / "templates" / "runbook.md")
SECTIONS = (
    Section("runbooks", "Runbooks", ("technicians",), "Faults."),
    Section("runbooks/av", "Audio-visual", ("technicians",), "AV.", "AV"),
    Section("procedures", "Procedures", ("technicians",), "How the team works."),
)
RUNBOOK = """---
id: RB-AV-001
title: "Projector shows no signal"
equipment: [laser-projector]
status: draft
reviewed: 2026-10-29
---

# Projector shows no signal

The projector is on but shows no picture.

## Symptoms

- "It says no signal."

## Before you start

- **Time:** about 5 minutes.

## Checks

1. Look at the panel. **Expected:** the source is selected. If not, go to
   step 1 of [Fix](#fix).
2. Look at the switcher. **Expected:** its light is lit. If not, go to
   [Escalate](#escalate).

## Fix

1. Select the source. **Expected:** the picture appears.
2. If it does not, escalate.

## Escalate

Escalate if the fix does not hold: to AV engineering, through the
[escalation matrix](../../procedures/escalation-matrix.md).

## Close the ticket

Record the room, what you found, what you did, and this runbook's
identifier, so a repeat fault can be traced.
"""
MATRIX = """# Escalation matrix

## The roles

### AV engineering

Repairs the room's equipment.
"""
INDEX = """# Audio-visual

| Identifier | Runbook |
| --- | --- |
| RB-AV-001 | [Projector shows no signal](rb-av-001-projector-shows-no-signal.md) |
"""
NAME = "rb-av-001-projector-shows-no-signal.md"


def _docs(tmp_path: Path, page: str = RUNBOOK, matrix: str | None = MATRIX) -> Path:
    docs = tmp_path / "docs"
    (docs / "runbooks" / "av").mkdir(parents=True)
    (docs / "procedures").mkdir()
    (docs / "runbooks" / "av" / NAME).write_text(page, encoding="utf-8")
    (docs / "runbooks" / "av" / "index.md").write_text(INDEX, encoding="utf-8")
    if matrix is not None:
        (docs / "procedures" / "escalation-matrix.md").write_text(matrix, encoding="utf-8")
    return docs


def _sections(docs: Path) -> list[str]:
    entries = runbook.catalog(docs, SECTIONS, ["laser-projector"])
    return validate.sections(docs, entries, TEMPLATE)


def test_a_runbook_that_follows_the_template_and_the_matrix_has_no_problems(
    tmp_path: Path,
) -> None:
    assert _sections(_docs(tmp_path)) == []


@pytest.mark.parametrize(
    ("old", "new", "message"),
    [
        ("## Symptoms\n", "## Symptom\n", "its sections are ['Symptom'"),
        ("## Before you start\n\n- **Time:** about 5 minutes.\n",
         "## Before you start\n\n", "Before you start is empty"),
        ("- **Time:** about 5 minutes.", "- **Time:** about N minutes.",
         "Before you start still has the template's line '- **Time:** about N minutes.'"),
        ("**Expected:** the source is selected.", "The source is selected.",
         "Checks step 1 does not say what to expect"),
        ("If not, go to\n   [Escalate](#escalate).", "If not, escalate.",
         "Checks step 2 does not link where to go if it fails"),
        ("**Expected:** the picture appears.", "The picture appears.",
         "Fix step 1 neither says what to expect nor escalates"),
        ("step 1 of [Fix](#fix)", "step 3 of [Fix](#fix)",
         "Checks names step 3 of Fix, which has 2"),
        ("[escalation matrix](../../procedures/escalation-matrix.md)",
         "[Procedures](../../procedures/index.md)",
         "Escalate does not link the escalation matrix (../../procedures/escalation-matrix.md)"),
    ],
)  # fmt: skip
def test_each_departure_from_the_template_is_named(
    tmp_path: Path, old: str, new: str, message: str
) -> None:
    assert RUNBOOK.count(old) == 1
    docs = _docs(tmp_path, RUNBOOK.replace(old, new))
    problems = _sections(docs)
    assert len(problems) == 1, problems
    assert problems[0].startswith(f"{docs / 'runbooks' / 'av' / NAME}: {message}")


def test_an_escalation_naming_no_role_is_named_and_leaves_the_role_unnamed(
    tmp_path: Path,
) -> None:
    docs = _docs(
        tmp_path, RUNBOOK.replace("to AV engineering, through", "to the next team, through")
    )
    assert _sections(docs) == [
        f"{docs / 'runbooks' / 'av' / NAME}: Escalate names none of the matrix's roles: "
        "AV engineering",
        f"{docs / 'procedures' / 'escalation-matrix.md'}: "
        "no runbook names the role 'AV engineering'",
    ]


def test_a_check_with_no_steps_is_named(tmp_path: Path) -> None:
    start = RUNBOOK.index("1. Look at the panel")
    end = RUNBOOK.index("## Fix")
    docs = _docs(tmp_path, RUNBOOK[:start] + "Look around.\n\n" + RUNBOOK[end:])
    assert any(p.endswith(": Checks has no numbered steps") for p in _sections(docs))


@pytest.mark.parametrize(
    "link",
    [
        "../../procedures/./escalation-matrix.md",
        "../av/../../procedures/escalation-matrix.md",
        "../../procedures/escalation-matrix.md#av-engineering",
        "../../procedures/escalation%2Dmatrix.md",
    ],
)
def test_a_link_to_the_matrix_counts_however_it_is_written(tmp_path: Path, link: str) -> None:
    page = RUNBOOK.replace("(../../procedures/escalation-matrix.md)", f"({link})")
    assert _sections(_docs(tmp_path, page)) == []


def test_a_step_reference_may_break_across_lines(tmp_path: Path) -> None:
    docs = _docs(tmp_path, RUNBOOK.replace("go to\n   step 1 of", "go to step\n   9 of"))
    assert [p.split(": ", 1)[1] for p in _sections(docs)] == [
        "Checks names step 9 of Fix, which has 2"
    ]


def test_a_runbook_missing_from_its_category_s_index_is_named(tmp_path: Path) -> None:
    docs = _docs(tmp_path)
    (docs / "runbooks" / "av" / "index.md").write_text("# Audio-visual\n", encoding="utf-8")
    assert _sections(docs) == [
        f"{docs / 'runbooks' / 'av' / NAME}: {docs / 'runbooks' / 'av' / 'index.md'} has no row "
        f"'| RB-AV-001 | [Projector shows no signal]({NAME}) |'"
    ]


def test_a_missing_matrix_is_one_problem_and_skips_the_role_check(tmp_path: Path) -> None:
    docs = _docs(tmp_path, matrix=None)
    assert _sections(docs) == [
        f"{docs / 'procedures' / 'escalation-matrix.md'} is missing: "
        "the escalation matrix runbooks escalate through"
    ]


def test_a_matrix_that_is_not_utf_8_is_a_problem_not_a_crash(tmp_path: Path) -> None:
    docs = _docs(tmp_path)
    (docs / "procedures" / "escalation-matrix.md").write_bytes(b"# Escalation\xff matrix\n")
    assert _sections(docs) == [f"{docs / 'procedures' / 'escalation-matrix.md'} is not UTF-8 text"]


def test_a_role_no_runbook_names_is_named(tmp_path: Path) -> None:
    docs = _docs(tmp_path, matrix=MATRIX + "\n### Facilities\n\nPower and furniture.\n")
    assert _sections(docs) == [
        f"{docs / 'procedures' / 'escalation-matrix.md'}: no runbook names the role 'Facilities'"
    ]


def test_a_matrix_with_no_roles_is_named(tmp_path: Path) -> None:
    docs = _docs(tmp_path, matrix="# Escalation matrix\n\n## Who takes what\n\n### Shift lead\n")
    assert _sections(docs) == [
        f"{docs / 'procedures' / 'escalation-matrix.md'} defines no roles: "
        "a '### ' heading under '## The roles'"
    ]


def test_roles_are_the_headings_under_the_roles_outside_code() -> None:
    matrix = (
        "## Who\n### Not one\n## The roles\n### Shift lead\n```\n### Not one\n```\n"
        "### Facilities\n## After\n### Nor this\n"
    )
    assert validate.roles(matrix) == ["Shift lead", "Facilities"]


def test_a_role_is_named_in_any_case_across_a_line_break_as_whole_words() -> None:
    assert validate.names("to the Service\n  Desk, through", "Service desk")
    assert not validate.names("to the service desks", "Service desk")
    assert not validate.names("to the servicedesk", "Service desk")


def test_the_command_lists_problems_and_exits_1(tmp_path: Path, capsys, monkeypatch) -> None:
    monkeypatch.chdir(ROOT)
    assert validate.main([]) == 0
    assert capsys.readouterr().out.endswith("\n0 problems\n")
    docs = _docs(tmp_path, RUNBOOK.replace("**Expected:** the picture appears.", "It appears."))
    code = validate.main(["--docs", str(docs)])
    out, err = capsys.readouterr()
    assert code == 1
    assert "Fix step 1 neither says what to expect nor escalates" in err
    # One runbook, for one kind of AV equipment, leaves the other 31 kinds uncovered.
    assert "coverage: Wall network port (wall-port), in 220 rooms (ALD-101" in err
    assert "pieces and 1 of 32 kinds of equipment are covered" in out
    # The tree has no home page, so none of its pages is reached.
    assert f"{(docs / 'runbooks' / 'av' / NAME).resolve()} is not reached by following" in err
    assert "links: 4 links (2 to a heading) on 3 pages followed; 0 of 3 pages reached" in out
    assert out.endswith(f"\n{len(err.splitlines())} problems\n")


ROOMS = Inventory(
    buildings=(Building("ALD", "Alder Hall"),),
    equipment=(
        Equipment("laser-projector", "Laser projector", "AV", "projector"),
        Equipment("webcam", "Webcam", "PER", "camera"),
        Equipment("wall-port", "Wall port", "NET", "network"),
    ),
    profiles=(),
    rooms=(
        Room("ALD", "101", "standard", 30, (("laser-projector", 1), ("webcam", 2))),
        Room("ALD", "102", "standard", 30, (("laser-projector", 1),)),
        Room("ALD", "103", "standard", 30, (("laser-projector", 2), ("webcam", 1))),
        Room("ALD", "104", "standard", 30, (("webcam", 1),)),
        Room("ALD", "105", "standard", 30, (("webcam", 1),)),
    ),
)
WEBCAM_GAP = (
    "coverage: Webcam (webcam), in 4 rooms (ALD-101, ALD-103, ALD-104 and 1 more), "
    "has no PER runbook that is not retired"
)


def _entry(identifier: str, equipment: list[str], status: str = "draft") -> runbook.Entry:
    return runbook.Entry(identifier, "A fault", tuple(equipment), status, Path("runbooks/x.md"))


def test_equipment_that_every_room_has_covered_counts_every_room_and_piece() -> None:
    entries = [_entry("RB-AV-001", ["laser-projector"]), _entry("RB-PER-001", ["webcam"]),
               _entry("RB-NET-001", ["wall-port"])]  # fmt: skip
    # The wall port is in no room, so it is not one of the kinds counted, covered or not.
    assert validate.coverage(ROOMS, entries) == (validate.Coverage((5, 5), (9, 9), (2, 2)), [])


@pytest.mark.parametrize(
    "webcam",
    [
        [],
        [_entry("RB-PER-001", ["webcam"], status="retired")],
        [_entry("RB-AV-002", ["webcam"])],
    ],
    ids=["no runbook", "retired", "another category"],
)
def test_a_kind_with_no_runbook_of_its_own_category_in_use_is_a_gap(webcam) -> None:
    entries = [_entry("RB-AV-001", ["laser-projector"]), *webcam]
    assert validate.coverage(ROOMS, entries) == (
        validate.Coverage((1, 5), (4, 9), (1, 2)),
        [WEBCAM_GAP],
    )


def test_a_gap_in_three_rooms_or_fewer_lists_them_all() -> None:
    rooms = Inventory(ROOMS.buildings, ROOMS.equipment, (), ROOMS.rooms[:3])
    covers, gaps = validate.coverage(rooms, [_entry("RB-AV-001", ["laser-projector"])])
    assert covers == validate.Coverage((1, 3), (4, 7), (1, 2))
    assert gaps == [WEBCAM_GAP.replace("4 rooms (ALD-101, ALD-103, ALD-104 and 1 more)",
                                       "2 rooms (ALD-101, ALD-103)")]  # fmt: skip


@pytest.mark.parametrize(
    ("heading", "expected"),
    [
        ("Shift lead", "shift-lead"),
        (" Shift lead ", "shift-lead"),
        ("Stage 1: learn the ground", "stage-1-learn-the-ground"),
        ("Teaching-technology team", "teaching-technology-team"),
        ("The `runbook new` command, **in short**", "the-runbook-new-command-in-short"),
        ("See [Rooms](rooms/index.md) first", "see-rooms-first"),
        ("ALD-104", "ald-104"),
        ("What's checked?", "whats-checked"),
    ],
)
def test_a_heading_s_anchor_is_github_s(heading: str, expected: str) -> None:
    assert validate.anchor(heading) == expected


def test_a_page_s_anchors_number_a_repeated_heading_and_skip_code() -> None:
    page = "# Title\n\n## Part\n\n```\n## Not a heading\n```\n\n## Part\n\n### Part ###\n"
    assert validate.anchors(page) == {"title", "part", "part-1", "part-2"}


HOME = "# Home\n\n[A](a.md) and [B's part](sub/b.md#part-1) and [web](https://example.org/x.md)\n"
A = "# A\n\n## Part one\n\nBack to [the part](#part-one) or [home](index.md#home).\n"
B = "# B\n\n## Part\n\n## Part\n\n`[shown](missing.md)`\n\n    [indented](missing.md)\n"


def _site(tmp_path: Path, **pages: str) -> Path:
    docs = tmp_path / "docs"
    (docs / "sub").mkdir(parents=True)
    for name, text in {"index.md": HOME, "a.md": A, "sub/b.md": B, **pages}.items():
        if text is not None:
            (docs / name).write_text(text, encoding="utf-8")
    return docs


def test_links_that_reach_their_files_and_headings_have_no_problems(tmp_path: Path) -> None:
    # The web link is not followed; links shown as code are not links.
    assert validate.links(_site(tmp_path)) == (validate.Links(3, 4, 3, 3), [])


@pytest.mark.parametrize(
    ("page", "old", "new", "message"),
    [
        ("a.md", "](#part-one)", "](#part-two)",
         "a.md:5: #part-two: a.md has no heading #part-two"),
        ("index.md", "(sub/b.md#part-1)", "(sub/b.md#part-2)",
         "index.md:3: sub/b.md#part-2: b.md has no heading #part-2"),
        ("index.md", "(a.md)", "(c.md)", "index.md:3: c.md reaches no file"),
        ("index.md", "(a.md)", "(sub)", "index.md:3: sub reaches no file"),
        ("a.md", "(index.md#home)", "(../outside.md)", "a.md:5: ../outside.md leads out of "),
    ],
)  # fmt: skip
def test_each_link_that_reaches_nothing_is_named_with_its_line(
    tmp_path: Path, page: str, old: str, new: str, message: str
) -> None:
    (tmp_path / "outside.md").write_text("# Outside\n", encoding="utf-8")
    text = {"index.md": HOME, "a.md": A}[page]
    assert text.count(old) == 1
    docs = _site(tmp_path, **{page: text.replace(old, new)})
    _, problems = validate.links(docs)
    # The message starts with the page's name, which the problem gives as its full path.
    assert problems[0].startswith(f"{(docs / page).resolve()}{message[len(page) :]}")


def test_a_page_no_link_leads_to_is_named(tmp_path: Path) -> None:
    docs = _site(tmp_path, **{"index.md": HOME.replace("[A](a.md) and ", "")})
    count, problems = validate.links(docs)
    assert count.reached == 2
    assert problems == [
        f"{(docs / 'a.md').resolve()} is not reached by following links from "
        f"{(docs / 'index.md').resolve()}"
    ]


def test_without_a_home_page_no_page_is_reached(tmp_path: Path) -> None:
    docs = _site(tmp_path, **{"index.md": None})
    count, problems = validate.links(docs)
    assert count == validate.Links(2, 2, 2, 0)
    assert len(problems) == 3  # index.md#home reaches no file, and neither page is reached
    assert problems[0].endswith("index.md#home reaches no file")


def test_a_link_s_percent_escapes_are_decoded(tmp_path: Path) -> None:
    home = HOME.replace("[A](a.md)", "[A](a.md) [C](my%20page.md#part)")
    docs = _site(tmp_path, **{"index.md": home, "my page.md": "# C\n\n## Part\n"})
    assert validate.links(docs) == (validate.Links(4, 5, 4, 4), [])
    (docs / "my page.md").unlink()
    assert validate.links(docs)[1] == [
        f"{(docs / 'index.md').resolve()}:3: my%20page.md#part reaches no file"
    ]


def test_a_page_that_is_not_utf_8_is_a_problem_not_a_crash(tmp_path: Path) -> None:
    docs = _site(tmp_path)
    (docs / "sub" / "b.md").write_bytes(b"# B\xff\n")
    _, problems = validate.links(docs)
    assert problems == [f"{(docs / 'sub' / 'b.md').resolve()} is not UTF-8 text"]
