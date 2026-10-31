"""The repository's own docs/ against its own structure.toml, and its runbooks."""

import re
from collections import Counter
from pathlib import Path

import pytest

from classroom_runbooks import inventory, runbook, validate
from classroom_runbooks.structure import check, links, load

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = load(ROOT / "structure.toml")
INVENTORY = inventory.load(ROOT / "inventory", [s.prefix for s in SECTIONS if s.prefix])
EQUIPMENT = INVENTORY.equipment


@pytest.fixture(scope="module")
def runbooks() -> tuple[runbook.Entry, ...]:
    """The runbooks, read once; a problem in one fails the tests that read them, not all."""
    return runbook.catalog(ROOT / "docs", SECTIONS, [e.id for e in EQUIPMENT])


def test_the_docs_follow_the_structure() -> None:
    assert check(SECTIONS, ROOT / "docs") == []


def test_runbook_categories_and_only_they_have_prefixes() -> None:
    for s in SECTIONS:
        assert (s.prefix is not None) == (s.parent == "runbooks"), s.path
    assert [s.prefix for s in SECTIONS if s.prefix] == ["AV", "NET", "PER", "ACC"]


def test_the_architecture_page_lists_every_section() -> None:
    page = (ROOT / "docs" / "contributing" / "information-architecture.md").read_text(
        encoding="utf-8"
    )
    for s in SECTIONS:
        assert f"| {s.title} | `{s.path}/` |" in page, s.path


def test_the_template_page_shows_the_template_as_it_is() -> None:
    page = (ROOT / "docs" / "contributing" / "runbook-template.md").read_text(encoding="utf-8")
    template = (ROOT / "templates" / "runbook.md").read_text(encoding="utf-8")
    shown = page.split("````markdown\n", 1)[1].split("\n````", 1)[0] + "\n"
    assert shown == template


def test_the_template_page_explains_every_field_and_section() -> None:
    page = (ROOT / "docs" / "contributing" / "runbook-template.md").read_text(encoding="utf-8")
    for field in runbook.FIELDS:
        assert f"| `{field}` |" in page, field
    rows = [line.split(" | ")[0][2:] for line in page.splitlines() if line.startswith("| ")]
    assert [row for row in rows if row in runbook.SECTIONS] == list(runbook.SECTIONS)


def test_the_template_s_links_reach_a_file_from_a_runbook_s_folder() -> None:
    template = (ROOT / "templates" / "runbook.md").read_text(encoding="utf-8")
    targets = links(template)
    assert targets
    for s in (s for s in SECTIONS if s.prefix):
        for target in targets:
            assert (ROOT / "docs" / s.path / target).is_file(), (s.path, target)


def test_the_docs_pass_the_validator(runbooks: tuple[runbook.Entry, ...]) -> None:
    assert len(runbooks) >= 29
    template = runbook.read(ROOT / "templates" / "runbook.md")
    assert validate.sections(ROOT / "docs", runbooks, template) == []
    covers, gaps = validate.coverage(INVENTORY, runbooks)
    assert gaps == []
    assert covers.kinds == (len(EQUIPMENT), len(EQUIPMENT))
    assert covers.rooms == (len(INVENTORY.rooms), len(INVENTORY.rooms))
    followed, broken = validate.links(ROOT / "docs")
    assert broken == []
    assert followed.reached == followed.pages > len(SECTIONS)


def _matrix() -> str:
    return (ROOT / "docs" / "procedures" / "escalation-matrix.md").read_text(encoding="utf-8")


def test_the_matrix_assigns_each_of_its_roles_and_links_its_definition() -> None:
    roles = validate.roles(_matrix())
    assert len(roles) >= 6
    table = _matrix().split("\n## Who takes what\n", 1)[1].split("\n## ", 1)[0]
    linked = re.findall(r"\| \[([^]]+)\]\(#([^)]+)\) \|$", table, re.MULTILINE)
    assert sorted(linked) == sorted((role, role.lower().replace(" ", "-")) for role in roles)


def test_the_matrix_gives_each_kind_of_equipment_the_owners_its_runbooks_name(
    runbooks: tuple[runbook.Entry, ...],
) -> None:
    roles = [role for role in validate.roles(_matrix()) if role != "Shift lead"]
    table = _matrix().split("\n## By equipment\n", 1)[1].split("\n## ", 1)[0]
    rows = re.findall(r"^\| (.+?) \| (.+) \|$", table, re.MULTILINE)[2:]  # after the header
    assert [name for name, _ in rows] == [e.name for e in EQUIPMENT]
    sections = {e.id: dict(runbook.read(ROOT / "docs" / e.path).sections) for e in runbooks}
    for item, (name, owners) in zip(EQUIPMENT, rows, strict=True):
        listed = set(re.findall(r"\[([^]]+)\]\(#", owners))
        covering = [sections[e.id] for e in runbooks if item.id in e.equipment]
        escalated = {r for s in covering for r in roles if validate.names(s["Escalate"], r)}
        handed = {r for s in covering for r in roles if validate.names(s["Fix"], r)}
        # Every owner its runbooks escalate to, and none they do not hand the fault to.
        assert escalated <= listed <= escalated | handed, name


def test_the_first_runbooks_cover_what_four_rooms_in_five_have(
    runbooks: tuple[runbook.Entry, ...],
) -> None:
    page = ROOT / "docs" / "start" / "onboarding.md"
    first = page.read_text(encoding="utf-8").split("\n## The first runbooks\n", 1)[1]
    first = first.split("\n## ", 1)[0]
    by_path = {(ROOT / "docs" / e.path).resolve(): e for e in runbooks}
    # The section's links that are runbooks (it also links the room inventory).
    targets = [(page.parent / target).resolve() for target in links(first)]
    chosen = [by_path[target] for target in targets if target in by_path]
    assert len(chosen) == len(set(targets)) - 1
    for entry in chosen:
        assert f"[{entry.title}](" in first, entry.id
    rooms = Counter(item for room in INVENTORY.rooms for item, _ in room.equipment)
    common = {item for item, n in rooms.items() if 5 * n >= 4 * len(INVENTORY.rooms)}
    covered = {item for entry in chosen for item in entry.equipment}
    assert common and sorted(common - covered) == []
    # Each one covers something most rooms have, and every category has one.
    assert all(common & set(entry.equipment) for entry in chosen)
    assert {e.id.split("-")[1] for e in chosen} == {s.prefix for s in SECTIONS if s.prefix}


def test_the_readme_quotes_what_the_validator_prints(capsys, monkeypatch) -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    quoted = readme.split("\n## The validator\n", 1)[1].split("```text\n", 1)[1]
    monkeypatch.chdir(ROOT)
    assert validate.main([]) == 0
    assert quoted.split("```", 1)[0] == capsys.readouterr().out
