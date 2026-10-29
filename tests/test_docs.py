"""The repository's own docs/ against its own structure.toml, and its runbooks."""

import re
from pathlib import Path

from classroom_runbooks import inventory, runbook
from classroom_runbooks.structure import check, links, load

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = load(ROOT / "structure.toml")
EQUIPMENT = inventory.load(ROOT / "inventory", [s.prefix for s in SECTIONS if s.prefix]).equipment
RUNBOOKS = runbook.catalog(ROOT / "docs", SECTIONS, [e.id for e in EQUIPMENT])
# A numbered step: its number and its text, up to the next step or the section's end.
_STEP = re.compile(r"^[0-9]+\. (.*?)(?=^[0-9]+\. |\Z)", re.MULTILINE | re.DOTALL)
_ANCHOR = re.compile(r"\]\(#([^)]*)\)")


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


def test_every_runbook_fills_the_template_s_sections_in_order() -> None:
    template = runbook.parse((ROOT / "templates" / "runbook.md").read_text(encoding="utf-8"))
    placeholders = [line.strip() for _, body in template.sections for line in body.splitlines()]
    assert RUNBOOKS
    for entry in RUNBOOKS:
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


def test_every_step_says_what_to_expect_and_a_check_where_to_go_if_not() -> None:
    for entry in RUNBOOKS:
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
        assert "../../procedures/index.md" in sections["Escalate"], entry.id


def test_a_runbook_s_links_within_the_page_name_its_sections() -> None:
    for entry in RUNBOOKS:
        page = runbook.read(ROOT / "docs" / entry.path)
        anchors = {name.lower().replace(" ", "-") for name, _ in page.sections}
        text = (ROOT / "docs" / entry.path).read_text(encoding="utf-8")
        for anchor in _ANCHOR.findall(text):
            assert anchor in anchors, (entry.id, anchor)


def test_each_category_s_index_lists_its_runbooks_by_identifier_and_title() -> None:
    for entry in RUNBOOKS:
        index = (ROOT / "docs" / entry.path.parent / "index.md").read_text(encoding="utf-8")
        assert f"| {entry.id} | [{entry.title}]({entry.path.name}) |" in index, entry.id
