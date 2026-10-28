import datetime
from pathlib import Path

import pytest

from classroom_runbooks.runbook import (
    FIELDS,
    SECTIONS,
    Page,
    RunbookError,
    main,
    new,
    next_number,
    parse,
    read,
    slug,
)

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = (ROOT / "templates" / "runbook.md").read_text(encoding="utf-8")
DAY = datetime.date(2026, 10, 28)
KNOWN = ("laser-projector", "projection-screen", "wall-port")
PAGE = """---
id: RB-AV-001
title: Projector shows no signal
equipment: [laser-projector]
status: current
reviewed: 2026-10-01
---

# Projector shows no signal

What this fixes.

## Symptoms

- Blue screen.

## Checks

```text
## not a section
# not the heading
```

1. Check the input.
"""


def test_a_page_is_read_into_front_matter_heading_and_sections() -> None:
    page = parse(PAGE)
    assert page == Page(
        {"id": "RB-AV-001", "title": "Projector shows no signal",
         "equipment": ["laser-projector"], "status": "current",
         "reviewed": datetime.date(2026, 10, 1)},
        "Projector shows no signal",
        (("Symptoms", "- Blue screen."),
         ("Checks", "```text\n## not a section\n# not the heading\n```\n\n1. Check the input.")),
    )  # fmt: skip
    assert parse(PAGE.replace("\n", "\r\n")) == page


def test_the_template_has_every_field_and_section_in_order() -> None:
    page = parse(TEMPLATE)
    assert tuple(page.meta) == FIELDS
    assert tuple(name for name, _ in page.sections) == SECTIONS
    assert page.heading == page.meta["title"]
    assert all(body for _, body in page.sections)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", "its first line is '---'"),
        ("# Title\n", "its first line is '---'"),
        (" ---\nid: x\n---\n", "its first line is '---'"),
        ("---\nid: x\n", "no closing '---' line"),
        ("---\n---\n", "not a set of keys and values"),
        ("---\n- id\n---\n", "not a set of keys and values"),
        ("---\nid: [x\n---\n", "not YAML"),
        # Line 4 of the file, where the second id is.
        ("---\nid: a\ntitle: b\nid: c\n---\n",
         "the key 'id' is given twice\n  in \"<unicode string>\", line 4, column 1"),
        ("---\n1: a\ntrue: b\n---\n", "is given twice"),
        ("---\nid: !!python/object:os.system x\n---\n", "not YAML"),
    ],
)  # fmt: skip
def test_a_damaged_page_is_refused(text: str, expected: str) -> None:
    with pytest.raises(RunbookError) as caught:
        parse(text)
    assert expected in str(caught.value)


def test_front_matter_is_any_yaml_mapping_including_merge_keys() -> None:
    text = "---\nbase: &base {status: draft, reviewed: 2026-10-01}\n<<: *base\nid: x\n---\n"
    assert parse(text).meta == {
        "base": {"status": "draft", "reviewed": datetime.date(2026, 10, 1)},
        "status": "draft", "reviewed": datetime.date(2026, 10, 1), "id": "x",
    }  # fmt: skip


def test_sections_heading_and_fences_follow_markdown() -> None:
    page = parse("---\nid: x\n---\n\nIntro.\n\n# Heading\n\n## One\n\n# Not a heading\n~~~~\n"
                 "~~~\n## inside\n~~~~\n## Two\n```\n## open to the end\n")  # fmt: skip
    # The heading comes before the first section; a fence closes with as many of its marks.
    assert page.heading == "Heading"
    assert [name for name, _ in page.sections] == ["One", "Two"]
    assert page.sections[0][1] == "# Not a heading\n~~~~\n~~~\n## inside\n~~~~"
    # Only the first heading, and only before the sections.
    assert parse("---\nid: x\n---\n# First\n# Second\n## One\n").heading == "First"
    assert parse("---\nid: x\n---\n## Only\n# Late\n").heading is None
    # A fence may be indented up to three spaces; four make an indented code line.
    page = parse("---\nid: x\n---\n## One\n   ```\n## inside\n   ```\n    ```\n## Two\n")
    assert [name for name, _ in page.sections] == ["One", "Two"]


def test_a_file_already_there_is_never_overwritten(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A file the numbering does not see, such as an upper-case name on a case-blind disk.
    existing = tmp_path / "rb-av-001-no-signal.md"
    existing.write_text("kept\n", encoding="utf-8")
    monkeypatch.setattr("classroom_runbooks.runbook.next_number", lambda folder, prefix: 1)
    with pytest.raises(RunbookError, match="is already there; it is not overwritten"):
        new(TEMPLATE, tmp_path, "AV", "No signal", ["wall-port"], KNOWN, DAY)
    assert existing.read_text(encoding="utf-8") == "kept\n"


def test_a_file_is_read_or_its_problem_named(tmp_path: Path) -> None:
    path = tmp_path / "rb-av-001-x.md"
    path.write_text(PAGE, encoding="utf-8")
    assert read(path) == parse(PAGE)
    with pytest.raises(RunbookError, match="is missing"):
        read(tmp_path / "none.md")
    path.write_bytes(b"---\n\xff\n---\n")
    with pytest.raises(RunbookError, match="is not UTF-8 text"):
        read(path)
    path.write_text("# no front matter\n", encoding="utf-8")
    with pytest.raises(RunbookError, match=r"rb-av-001-x\.md: a runbook starts with front matter"):
        read(path)


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("Projector shows no signal", "projector-shows-no-signal"),
        ("Can't sign in: \"account locked\"", "can-t-sign-in-account-locked"),
        ("Wi-Fi drops every ~10 minutes", "wi-fi-drops-every-10-minutes"),
        ("Écran noir après mise à jour", "ecran-noir-apres-mise-a-jour"),
        ("投影机 no signal", "no-signal"),
        ("Audio processor and amplifier shows a fault light after a power cut today",
         "audio-processor-and-amplifier-shows-a-fault-light"),
        ("A" * 60, "a" * 50),
        # Nine words of 4 and one of 5 make exactly 50; the next word would not fit.
        ("abcd " * 9 + "efghi next", "abcd-" * 9 + "efghi"),
        ("!!!", ""),
    ],
)  # fmt: skip
def test_a_slug_is_the_title_s_words_cut_at_a_word(title: str, expected: str) -> None:
    assert slug(title) == expected
    assert len(slug(title)) <= 50


def test_the_next_number_follows_the_highest_file_whatever_its_status(tmp_path: Path) -> None:
    assert next_number(tmp_path, "AV") == 1
    for name in (
        "rb-av-001-a.md",
        "rb-av-003-retired.md",
        "rb-net-007-x.md",
        "index.md",
        "rb-av-9-short.md",
        "rb-av-004-draft.txt",
        "RB-AV-008-upper.md",
    ):
        (tmp_path / name).write_text("x", encoding="utf-8")  # fmt: skip
    assert next_number(tmp_path, "AV") == 4
    assert next_number(tmp_path, "NET") == 8
    assert next_number(tmp_path, "PER") == 1


def test_a_new_runbook_is_the_template_filled_in(tmp_path: Path) -> None:
    path = new(TEMPLATE, tmp_path, "AV", "Projector shows no signal",
               ["laser-projector", "projection-screen"], KNOWN, DAY)  # fmt: skip
    assert path == tmp_path / "rb-av-001-projector-shows-no-signal.md"
    assert b"\r" not in path.read_bytes()
    page = read(path)
    assert page.meta == {
        "id": "RB-AV-001", "title": "Projector shows no signal",
        "equipment": ["laser-projector", "projection-screen"], "status": "draft",
        "reviewed": DAY,
    }  # fmt: skip
    assert page.heading == "Projector shows no signal"
    assert page.sections == parse(TEMPLATE).sections
    second = new(TEMPLATE, tmp_path, "AV", "Projector shows no signal", ["wall-port"], KNOWN, DAY)
    assert second.name == "rb-av-002-projector-shows-no-signal.md"


@pytest.mark.parametrize(
    "title",
    ['Can\'t sign in: "account locked"', "# not a heading", "Wi-Fi: 50% packet loss #2",
     "Écran noir — no signal", "yes", "2026-10-28", "[1, 2]", "- item", "'quoted'", "\\path"],
)  # fmt: skip
def test_any_title_reads_back_as_written(tmp_path: Path, title: str) -> None:
    page = read(new(TEMPLATE, tmp_path, "AV", title, ["wall-port"], KNOWN, DAY))
    assert page.meta["title"] == title
    assert page.heading == title


@pytest.mark.parametrize(
    ("title", "equipment", "expected"),
    [
        ("", ["wall-port"], "one line of text"),
        (" Padded", ["wall-port"], "one line of text"),
        ("Two\nlines", ["wall-port"], "one line of text"),
        ("Two\rlines", ["wall-port"], "one line of text"),
        ("x" * 81, ["wall-port"], "at most 80 characters; this is 81"),
        ("???", ["wall-port"], "needs a letter or digit"),
        ("No signal", [], "name the equipment"),
        ("No signal", ["laser"], "not in the inventory's equipment: laser"),
        ("No signal", ["wall-port", "wall-port"], "given twice"),
    ],
)  # fmt: skip
def test_a_new_runbook_is_refused_for_a_bad_title_or_equipment(
    tmp_path: Path, title: str, equipment: list[str], expected: str
) -> None:
    with pytest.raises(RunbookError, match=expected):
        new(TEMPLATE, tmp_path, "AV", title, equipment, KNOWN, DAY)
    assert list(tmp_path.iterdir()) == []


def test_numbers_run_out_at_999_and_a_changed_template_is_refused(tmp_path: Path) -> None:
    (tmp_path / "rb-av-999-last.md").write_text("x", encoding="utf-8")
    with pytest.raises(RunbookError, match="RB-AV has used all 999 numbers"):
        new(TEMPLATE, tmp_path, "AV", "No signal", ["wall-port"], KNOWN, DAY)
    changed = TEMPLATE.replace("reviewed: YYYY-MM-DD", "reviewed: never")
    with pytest.raises(RunbookError, match="no longer has the line 'reviewed: YYYY-MM-DD'"):
        new(changed, tmp_path, "PER", "No signal", ["wall-port"], KNOWN, DAY)
    assert sorted(p.name for p in tmp_path.iterdir()) == ["rb-av-999-last.md"]


def test_the_command_writes_a_draft_into_the_category_s_folder(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    docs = tmp_path / "docs"
    (docs / "runbooks" / "av").mkdir(parents=True)
    args = ["--docs", str(docs), "--structure", str(ROOT / "structure.toml"),
            "--inventory", str(ROOT / "inventory"),
            "--template", str(ROOT / "templates" / "runbook.md")]  # fmt: skip
    assert main(["new", "AV", "Projector shows no signal", "--equipment", "laser-projector",
                 *args]) == 0  # fmt: skip
    path = docs / "runbooks" / "av" / "rb-av-001-projector-shows-no-signal.md"
    assert capsys.readouterr().out.splitlines()[0] == f"wrote {path}"
    assert read(path).meta["equipment"] == ["laser-projector"]
    assert read(path).meta["reviewed"] == datetime.date.today()
    assert main(["new", "XX", "No signal", "--equipment", "wall-port", *args]) == 1
    assert "'XX' is not a runbook category (AV, NET, PER, ACC)" in capsys.readouterr().err
    assert main(["new", "NET", "No link", "--equipment", "wall-port", *args]) == 1
    assert "error: " in capsys.readouterr().err  # the network folder is not there
    assert main(["new", "AV", "No signal", "--equipment", "projector", *args]) == 1
    assert "not in the inventory's equipment: projector" in capsys.readouterr().err
    broken = tmp_path / "inventory"
    broken.mkdir()
    assert main(["new", "AV", "No signal", "--equipment", "wall-port", *args[:4],
                 "--inventory", str(broken), *args[6:]]) == 1  # fmt: skip
    assert "the inventory has 4 problems" in capsys.readouterr().err
