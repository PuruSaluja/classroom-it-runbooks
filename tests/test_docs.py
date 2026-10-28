"""The repository's own docs/ against its own structure.toml."""

from pathlib import Path

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
    assert len(pages) == len(SECTIONS) + 2  # the home page and the architecture page
    for page in pages:
        for target in links(page.read_text(encoding="utf-8")):
            assert (page.parent / target).is_file(), f"{page}: {target}"


def test_the_architecture_page_lists_every_section() -> None:
    page = (ROOT / "docs" / "contributing" / "information-architecture.md").read_text(
        encoding="utf-8"
    )
    for s in SECTIONS:
        assert f"| {s.title} | `{s.path}/` |" in page, s.path
