"""The repository's own docs/ against its own structure.toml, and its runbooks."""

import re
from collections import Counter
from pathlib import Path

import pytest

from classroom_runbooks import inventory, runbook
from classroom_runbooks.structure import check, links, load

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = load(ROOT / "structure.toml")
INVENTORY = inventory.load(ROOT / "inventory", [s.prefix for s in SECTIONS if s.prefix])
EQUIPMENT = INVENTORY.equipment
# A numbered step's text, up to the next step or the section's end.
_STEP = re.compile(r"^[0-9]+\. (.*?)(?=^[0-9]+\. |\Z)", re.MULTILINE | re.DOTALL)
_ANCHOR = re.compile(r"\]\(#([^)]*)\)")
# "go to step 2 of [Fix](#fix)", which a line may break anywhere in.
_FIX_STEP = re.compile(r"step\s+([0-9]+)\s+of\s+\[Fix\]")


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


def test_every_relative_link_in_the_docs_reaches_a_file() -> None:
    pages = sorted((ROOT / "docs").rglob("*.md"))
    assert len(pages) >= len(SECTIONS) + 1
    for page in pages:
        for target in links(page.read_text(encoding="utf-8")):
            assert (page.parent / target).is_file(), f"{page}: {target}"


def test_every_page_is_reached_by_following_links_from_the_home_page() -> None:
    docs = ROOT / "docs"
    reached, todo = set(), [(docs / "index.md").resolve()]
    while todo:
        page = todo.pop()
        if page in reached or page.suffix != ".md":
            continue
        reached.add(page)
        text = page.read_text(encoding="utf-8")
        todo += [(page.parent / target).resolve() for target in links(text)]
    pages = {p.resolve() for p in docs.rglob("*.md")}
    assert sorted(map(str, pages - reached)) == []


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


def test_every_runbook_fills_the_template_s_sections_in_order(
    runbooks: tuple[runbook.Entry, ...],
) -> None:
    template = runbook.parse((ROOT / "templates" / "runbook.md").read_text(encoding="utf-8"))
    placeholders = [line.strip() for _, body in template.sections for line in body.splitlines()]
    assert runbooks
    for entry in runbooks:
        page = runbook.read(ROOT / "docs" / entry.path)
        assert tuple(name for name, _ in page.sections) == runbook.SECTIONS, entry.id
        assert all(body.strip() for _, body in page.sections), entry.id
        # The template's example lines are replaced, apart from its standard wording.
        kept = {"Escalate if the checks do not find the fault or the fix does not hold: who",
                "Record the room, what you found, what you did, and this runbook's",
                "identifier, so a repeat fault can be traced.", ""}  # fmt: skip
        for _, body in page.sections:
            for line in body.splitlines():
                assert line.strip() in kept or line.strip() not in placeholders, (entry.id, line)


def test_every_step_says_what_to_expect_and_a_check_where_to_go_if_not(
    runbooks: tuple[runbook.Entry, ...],
) -> None:
    for entry in runbooks:
        sections = dict(runbook.read(ROOT / "docs" / entry.path).sections)
        steps = _STEP.findall(sections["Checks"])
        assert steps, entry.id
        for number, step in enumerate(steps, 1):
            assert "**Expected:**" in step, (entry.id, number)
            assert "](" in step, (entry.id, number)
        actions = _STEP.findall(sections["Fix"])
        assert actions, entry.id
        # An action says what it should do; the step that hands the fault on need not.
        for number, step in enumerate(actions, 1):
            assert "**Expected:**" in step or "escalate" in step.lower(), (entry.id, number)
        assert "../../procedures/escalation-matrix.md" in sections["Escalate"], entry.id


def _matrix() -> str:
    return (ROOT / "docs" / "procedures" / "escalation-matrix.md").read_text(encoding="utf-8")


def _roles() -> list[str]:
    """The roles the escalation matrix defines: the headings under "The roles"."""
    roles = _matrix().split("\n## The roles\n", 1)[1]
    return [line[4:].strip() for line in roles.splitlines() if line.startswith("### ")]


def _names(text: str, role: str) -> bool:
    """Whether text names the role, in any case and across a line break."""
    words = r"\s+".join(map(re.escape, role.lower().split()))
    return re.search(rf"\b{words}\b", text.lower()) is not None


def test_the_matrix_assigns_each_of_its_roles_and_links_its_definition() -> None:
    roles = _roles()
    assert len(roles) >= 6
    table = _matrix().split("\n## Who takes what\n", 1)[1].split("\n## ", 1)[0]
    linked = re.findall(r"\| \[([^]]+)\]\(#([^)]+)\) \|$", table, re.MULTILINE)
    assert sorted(linked) == sorted((role, role.lower().replace(" ", "-")) for role in roles)


def test_every_escalation_names_a_role_the_matrix_defines(
    runbooks: tuple[runbook.Entry, ...],
) -> None:
    roles = _roles()
    for entry in runbooks:
        escalate = dict(runbook.read(ROOT / "docs" / entry.path).sections)["Escalate"]
        assert any(_names(escalate, role) for role in roles), entry.id


def test_every_role_the_matrix_defines_is_one_a_runbook_hands_faults_to(
    runbooks: tuple[runbook.Entry, ...],
) -> None:
    texts = [(ROOT / "docs" / entry.path).read_text(encoding="utf-8") for entry in runbooks]
    for role in _roles():
        assert any(_names(text, role) for text in texts), role


def test_a_runbook_s_links_within_the_page_name_its_sections(
    runbooks: tuple[runbook.Entry, ...],
) -> None:
    for entry in runbooks:
        page = runbook.read(ROOT / "docs" / entry.path)
        anchors = {name.lower().replace(" ", "-") for name, _ in page.sections}
        text = (ROOT / "docs" / entry.path).read_text(encoding="utf-8")
        for anchor in _ANCHOR.findall(text):
            assert anchor in anchors, (entry.id, anchor)


def test_a_step_of_fix_that_a_runbook_names_is_there(
    runbooks: tuple[runbook.Entry, ...],
) -> None:
    named = 0
    for entry in runbooks:
        page = runbook.read(ROOT / "docs" / entry.path)
        steps = len(_STEP.findall(dict(page.sections)["Fix"]))
        for _, body in page.sections:
            for number in _FIX_STEP.findall(body):
                assert 1 <= int(number) <= steps, (entry.id, number)
                named += 1
    assert named >= len(runbooks)


def test_each_category_s_index_lists_its_runbooks_by_identifier_and_title(
    runbooks: tuple[runbook.Entry, ...],
) -> None:
    for entry in runbooks:
        index = (ROOT / "docs" / entry.path.parent / "index.md").read_text(encoding="utf-8")
        assert f"| {entry.id} | [{entry.title}]({entry.path.name}) |" in index, entry.id


def test_every_piece_of_equipment_has_a_runbook_in_its_category(
    runbooks: tuple[runbook.Entry, ...],
) -> None:
    covered: dict[str, set[str]] = {}
    for entry in (e for e in runbooks if e.status != "retired"):
        for item in entry.equipment:
            covered.setdefault(item, set()).add(entry.id.split("-")[1])
    # A runbook of another category may cover it too, but its own category has one.
    assert [e.id for e in EQUIPMENT if e.category not in covered.get(e.id, set())] == []


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
