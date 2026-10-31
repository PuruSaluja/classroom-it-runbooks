"""The site's navigation and build: mkdocs.yml with the hooks in classroom_runbooks.site."""

import re
from pathlib import Path

import pytest
from mkdocs.commands.build import build
from mkdocs.config import load_config
from mkdocs.exceptions import Abort

from classroom_runbooks import site, structure, validate

ROOT = Path(__file__).resolve().parents[1]
SECTIONS = structure.load(ROOT / "structure.toml")
HOOKS = ROOT / "src" / "classroom_runbooks" / "site.py"
_HEADING_ID = re.compile(r'<h([1-6]) id="([^"]+)"')


def flatten(entries: list) -> list[str]:
    pages = []
    for entry in entries:
        if isinstance(entry, str):
            pages.append(entry)
        else:
            (children,) = entry.values()
            pages += flatten(children)
    return pages


def titles(entries: list) -> list[str]:
    found = []
    for entry in entries:
        if isinstance(entry, dict):
            ((title, children),) = entry.items()
            found += [title, *titles(children)]
    return found


def make_site(folder: Path, pages: dict[str, str]) -> Path:
    """A small site in ``folder``: one Procedures section, and the repository's hooks."""
    (folder / "structure.toml").write_text(
        '[[section]]\npath = "procedures"\ntitle = "Procedures"\n'
        'audience = ["technicians"]\npurpose = "How the team works."\n',
        encoding="utf-8",
    )
    (folder / "mkdocs.yml").write_text(
        f"site_name: Test\nstrict: true\nhooks:\n  - {HOOKS.as_posix()}\n"
        "validation:\n  anchors: warn\n  omitted_files: warn\n"
        "markdown_extensions:\n  - toc\n",
        encoding="utf-8",
    )
    for name, text in pages.items():
        (folder / "docs" / name).parent.mkdir(parents=True, exist_ok=True)
        (folder / "docs" / name).write_text(text, encoding="utf-8")
    return folder / "mkdocs.yml"


@pytest.fixture(scope="module")
def built(tmp_path_factory) -> Path:
    """The repository's site, built once, strictly."""
    out = tmp_path_factory.mktemp("site")
    config = load_config(config_file=str(ROOT / "mkdocs.yml"), site_dir=str(out))
    build(config)
    # The hooks set the navigation as the build starts.
    assert config.nav == site.nav(SECTIONS, ROOT / "docs")
    return out


def test_the_navigation_holds_every_page_once_in_the_structure_s_order() -> None:
    entries = site.nav(SECTIONS, ROOT / "docs")
    pages = flatten(entries)
    assert sorted(pages) == sorted(p.relative_to(ROOT / "docs").as_posix()
                                   for p in (ROOT / "docs").rglob("*.md"))  # fmt: skip
    assert len(pages) == len(set(pages))
    assert pages[0] == "index.md"
    assert titles(entries) == [s.title for s in SECTIONS]
    # A section's index comes first, then its own pages, then the sections under it.
    for s in SECTIONS:
        (inside,) = [e[s.title] for e in _walk(entries) if isinstance(e, dict) and s.title in e]
        assert inside[0] == f"{s.path}/index.md"
        own = [e for e in inside if isinstance(e, str)]
        assert inside[: len(own)] == own


def _walk(entries: list):
    for entry in entries:
        yield entry
        if isinstance(entry, dict):
            yield from _walk(next(iter(entry.values())))


def test_a_section_s_pages_follow_the_order_its_index_links_them(tmp_path: Path) -> None:
    folder = tmp_path / "docs" / "procedures"
    folder.mkdir(parents=True)
    for name in ("a.md", "b.md", "c.md", "d.md"):
        (folder / name).write_text(f"# {name}\n", encoding="utf-8")
    (folder / "index.md").write_text(
        "# Procedures\n\n[C](c.md), [A again](./a.md#x), [A](a.md), `[B](b.md)`, "
        "[out](https://example.com/d.md)\n",
        encoding="utf-8",
    )
    section = structure.Section("procedures", "Procedures", ("technicians",), "How.")
    assert site.nav([section], tmp_path / "docs") == [
        "index.md",
        {"Procedures": ["procedures/index.md", "procedures/c.md", "procedures/a.md",
                        "procedures/b.md", "procedures/d.md"]},
    ]  # fmt: skip
    pages = flatten(site.nav(SECTIONS, ROOT / "docs"))
    assert pages[pages.index("contributing/index.md") :][:4] == [
        "contributing/index.md",
        "contributing/information-architecture.md",
        "contributing/runbook-template.md",
        "contributing/authoring-conventions.md",
    ]


def test_every_page_is_built_with_the_anchors_the_validator_checks(built: Path) -> None:
    docs = ROOT / "docs"
    for page in sorted(docs.rglob("*.md")):
        relative = page.relative_to(docs).with_suffix("")
        html = built / (relative.parent if relative.name == "index" else relative) / "index.html"
        ids = {i for _, i in _HEADING_ID.findall(html.read_text(encoding="utf-8"))}
        # The pages' anchors are all headings' (no page has an HTML id of its own).
        assert ids == validate.anchors(page.read_text(encoding="utf-8")), page


def test_the_site_has_search_and_the_sections_in_its_navigation(built: Path) -> None:
    assert (built / "search" / "search_index.json").is_file()
    home = (built / "index.html").read_text(encoding="utf-8")
    for s in (s for s in SECTIONS if s.parent is None):
        assert f'href="{s.path}/"' in home, s.path
    assert "fonts.googleapis.com" not in home


def test_headings_get_github_s_anchors_and_a_repeat_is_numbered(tmp_path: Path) -> None:
    config = make_site(tmp_path, {
        "index.md": "# Home\n\n[Procedures](procedures/index.md)\n",
        "procedures/index.md": "# Procedures\n\n## Fix — now\n\n## Fix — now\n\n"
                               "[again](#fix--now-1)\n",
    })  # fmt: skip
    out = tmp_path / "out"
    build(load_config(config_file=str(config), site_dir=str(out)))
    html = (out / "procedures" / "index.html").read_text(encoding="utf-8")
    assert [i for _, i in _HEADING_ID.findall(html)][-2:] == ["fix--now", "fix--now-1"]


def test_a_strict_build_fails_on_an_anchor_that_names_nothing(tmp_path: Path) -> None:
    config = make_site(tmp_path, {
        "index.md": "# Home\n\n[Procedures](procedures/index.md#no-such-heading)\n",
        "procedures/index.md": "# Procedures\n\n## Fix\n",
    })  # fmt: skip
    with pytest.raises(Abort):
        build(load_config(config_file=str(config), site_dir=str(tmp_path / "out")))
