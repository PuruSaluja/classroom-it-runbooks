"""The repository's own docs/ against its own structure.toml."""

from pathlib import Path

from classroom_runbooks import runbook
from classroom_runbooks.structure import check, links, load

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = load(ROOT / "structure.toml")


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
