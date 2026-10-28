from pathlib import Path

import pytest

from classroom_runbooks.structure import (
    Section,
    StructureError,
    check,
    code_lines,
    links,
    load,
    main,
    parse,
    split_lines,
    tree,
)

GOOD = """
[[section]]
path = "start"
title = "Start here"
audience = ["new technicians"]
purpose = "The first week."

[[section]]
path = "runbooks"
title = "Runbooks"
audience = ["technicians"]
purpose = "Faults and their fixes."

[[section]]
path = "runbooks/av"
title = "Audio-visual"
audience = ["technicians", "new technicians"]
purpose = "Projectors and displays."
prefix = "AV"
"""


def write_tree(docs: Path, sections, *, home_links=None) -> None:
    """A docs tree that follows ``sections``: each index titled, linking its children."""
    docs.mkdir(parents=True, exist_ok=True)
    top = [s for s in sections if s.parent is None] if home_links is None else home_links
    home = "# Home\n\n" + "".join(f"- [{s.title}]({s.path}/index.md)\n" for s in top)
    (docs / "index.md").write_text(home, encoding="utf-8")
    for s in sections:
        folder = docs / s.path
        folder.mkdir(parents=True, exist_ok=True)
        children = [c for c in sections if c.parent == s.path]
        body = "".join(f"- [{c.title}]({c.path.rsplit('/', 1)[1]}/index.md)\n" for c in children)
        (folder / "index.md").write_text(f"# {s.title}\n\n{body}", encoding="utf-8")


def test_a_structure_is_read_with_each_section_s_parent() -> None:
    sections = parse(GOOD)
    assert [s.path for s in sections] == ["start", "runbooks", "runbooks/av"]
    assert sections[2] == Section(
        "runbooks/av", "Audio-visual", ("technicians", "new technicians"),
        "Projectors and displays.", "AV",
    )  # fmt: skip
    assert [s.parent for s in sections] == [None, None, "runbooks"]
    assert tree(sections) == [
        "start/  Start here",
        "runbooks/  Runbooks",
        "  runbooks/av/  Audio-visual  [AV]",
    ]


def section(**fields) -> str:
    entry = {"path": '"start"', "title": '"Start"', "audience": '["technicians"]',
             "purpose": '"x"'} | fields  # fmt: skip
    return "[[section]]\n" + "".join(f"{k} = {v}\n" for k, v in entry.items() if v is not None)


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("[[section]\n", "not TOML"),
        ('title = "x"\n' + section(), "unknown keys title"),
        ("", "no \\[\\[section\\]\\] entries"),
        (section(owner='"me"'), "unknown keys owner"),
        (section(path=None), "path must be text"),
        (section(path='"Start"'), "lower-case words"),
        (section(path='"start/"'), "lower-case words"),
        (section(path='"../start"'), "lower-case words"),
        (section(path='"start here"'), "lower-case words"),
        (section(path='"assets"'), "kept for images"),
        (section(title='" Start"'), "spaces at an end"),
        (section(title='""'), "title must be text"),
        (section(audience="[]"), "audience is a list"),
        (section(audience='["students"]'), "audience is a list"),
        (section(audience='["leads", "leads"]'), "audience is a list"),
        (section(audience='"leads"'), "audience is a list"),
        (section(prefix='"av"'), "2 to 4 capital letters"),
        (section(prefix='"AUDIO"'), "2 to 4 capital letters"),
        (section(prefix="1"), "2 to 4 capital letters"),
        (section() + section(title='"Other"'), "the path start"),
        (section() + section(path='"other"'), "the title Start"),
        (section(prefix='"AV"') + section(path='"b"', title='"B"', prefix='"AV"'), "prefix AV"),
        (section(path='"runbooks/av"'), "under 'runbooks', which is not one"),
    ],
)
def test_a_structure_that_cannot_lay_out_the_docs_is_refused(text, message) -> None:
    with pytest.raises(StructureError, match=message):
        parse(text)


def test_a_tree_that_follows_the_structure_has_no_problems(tmp_path: Path) -> None:
    sections = parse(GOOD)
    write_tree(tmp_path / "docs", sections)
    (tmp_path / "docs" / "runbooks" / "av" / "assets").mkdir()
    (tmp_path / "docs" / "assets" / "diagrams").mkdir(parents=True)
    assert check(sections, tmp_path / "docs") == []
    (tmp_path / "docs" / "runbooks" / "myassets").mkdir()
    (problem,) = check(sections, tmp_path / "docs")
    assert problem.endswith("myassets is not a section in the structure")


def test_each_departure_from_the_structure_is_named(tmp_path: Path) -> None:
    sections = parse(GOOD)
    docs = tmp_path / "docs"
    write_tree(docs, sections)
    (docs / "start" / "index.md").unlink()
    (docs / "runbooks" / "av" / "index.md").write_text("# Audio visual\n", encoding="utf-8")
    (docs / "runbooks" / "network").mkdir()
    (docs / "runbooks" / "index.md").write_text("# Runbooks\n\nNo links.\n", encoding="utf-8")
    problems = check(sections, docs)
    assert len(problems) == 4
    assert "section 'Start here' has no index page" in problems[0]
    assert "starts '# Audio visual', not '# Audio-visual'" in problems[1]
    assert problems[2].endswith("network is not a section in the structure")
    assert "runbooks" in problems[3] and "does not link to runbooks/av/index.md" in problems[3]


def test_the_home_page_must_link_every_top_level_section(tmp_path: Path) -> None:
    sections = parse(GOOD)
    docs = tmp_path / "docs"
    write_tree(docs, sections, home_links=[sections[0]])
    (problem,) = check(sections, docs)
    assert problem.endswith("does not link to runbooks/index.md (Runbooks)")
    (docs / "index.md").unlink()
    (problem,) = check(sections, docs)
    assert problem.endswith("index.md is missing: the home page")


def test_a_page_with_no_text_is_named_as_untitled(tmp_path: Path) -> None:
    sections = parse(GOOD)
    write_tree(tmp_path, sections)
    (tmp_path / "start" / "index.md").write_text("", encoding="utf-8")
    assert check(sections, tmp_path) == [
        f"{tmp_path / 'start' / 'index.md'} starts '', not '# Start here'"
    ]


def test_links_are_relative_targets_without_anchors() -> None:
    text = (
        "[a](start/index.md) [b](./runbooks/index.md#faults) [c](https://example.org/x.md) "
        '[d](#top) [e](<av/index.md>) [f](av/index.md "Audio") [g](mailto:a@b.c)'
    )
    assert links(text) == {"start/index.md", "./runbooks/index.md", "av/index.md"}


def test_a_link_in_a_code_fence_is_shown_not_followed() -> None:
    text = (
        "[a](a.md)\n```markdown\n[b](b.md)\n```python\n[c](c.md)\n```\n[d](d.md)\n"
        "  ~~~~\n[e](e.md)\n~~~\n[f](f.md)\n~~~~~\n[g](g.md)\n    ```\n[h](h.md)\n```\n[i](i.md)\n"
    )
    # A fence closes on a line of only its own mark, at least as long; four spaces in is
    # not a fence; one left open runs to the end.
    assert links(text) == {"a.md", "d.md", "g.md", "h.md"}


def test_split_lines_breaks_at_lf_crlf_and_cr_only() -> None:
    assert split_lines("a\nb\r\nc\rd\x0ce\u2028f\x85g\n") == ["a", "b", "c", "d\x0ce\u2028f\x85g"]
    assert split_lines("") == []
    assert split_lines("a\n\n") == ["a", ""]
    assert split_lines("no end") == ["no end"]


def test_a_link_in_an_indented_code_block_is_shown_not_followed() -> None:
    text = "\n".join([
        "    [a](a.md)",      # indented at the top: code
        "text",
        "    [b](b.md)",      # continues the paragraph above: text
        "",
        "    [c](c.md)",      # after a blank line: code
        "",
        "    [d](d.md)",      # the same block, across a blank line
        "x",
        "- item",
        "",
        "    [e](e.md)",      # the item's own text, not code
        "",
        "para",
        "",
        "\t[f](f.md)",        # a tab counts as four spaces
        "",
        "1. step",
        "   [g](g.md)",       # under a numbered item
        "",
        "```",
        "    [h](h.md)",      # in a fence
        "```",
        "    [i](i.md)",      # straight after a fence: no paragraph is open, so code
        "# Heading",
        "    [j](j.md)",      # straight after a heading: code too
        "***",
        "    [k](k.md)",      # and after a thematic break
        "a line",
        "    [l](l.md)",      # but this continues the paragraph
    ])  # fmt: skip
    assert links(text) == {"b.md", "e.md", "g.md", "l.md"}


def test_a_link_in_a_code_span_is_shown_not_followed() -> None:
    text = "See `[x](x.md)` and [y](y.md); ``[z](z.md) ` still code`` [w](w.md); ` [v](v.md)"
    # A span closes with a run of as many backticks; a lone one opens nothing.
    assert links(text) == {"y.md", "w.md", "v.md"}


def test_a_prefix_or_path_ending_in_a_newline_is_refused() -> None:
    with pytest.raises(StructureError, match=r"a prefix is 2 to 4 capital letters, not 'AV\\n'"):
        parse(GOOD.replace('prefix = "AV"', 'prefix = "AV\\n"'))
    with pytest.raises(StructureError, match="a path is lower-case words"):
        parse(GOOD.replace('path = "runbooks/av"', 'path = "runbooks/av\\nx"'))


def test_code_lines_marks_each_fenced_line_and_its_fences() -> None:
    lines = ["text", "``` text", "code", "``` ", "text", "~~~", "```", "~~~ x", "~~~", "text"]
    assert code_lines(lines) == [False, True, True, True, False, True, True, True, True, False]
    # Only a fence's own mark closes it.
    assert code_lines(["```", "~~~", "in code", "```", "text"]) == [True] * 4 + [False]
    assert code_lines([]) == []


def test_a_link_counts_however_its_relative_path_is_written(tmp_path: Path) -> None:
    sections = parse(GOOD)
    docs = tmp_path / "docs"
    write_tree(docs, sections)
    (docs / "index.md").write_text(
        "# Home\n[s](./start/index.md#week-one) [r](runbooks/../runbooks/index.md)\n",
        encoding="utf-8",
    )
    assert check(sections, docs) == []


def test_the_command_prints_the_tree_and_exits_on_problems(tmp_path: Path, capsys) -> None:
    structure = tmp_path / "structure.toml"
    structure.write_text(GOOD, encoding="utf-8")
    docs = tmp_path / "docs"
    write_tree(docs, parse(GOOD))
    argv = ["--structure", str(structure), "--docs", str(docs)]
    assert main(argv) == 0
    out = capsys.readouterr()
    assert "  runbooks/av/  Audio-visual  [AV]" in out.out
    assert "3 sections; 0 problems" in out.out
    (docs / "start" / "index.md").unlink()
    assert main(argv) == 1
    out = capsys.readouterr()
    assert "problem: " in out.err and "3 sections; 1 problems" in out.out


def test_a_missing_or_unreadable_structure_is_named(tmp_path: Path, capsys) -> None:
    assert main(["--structure", str(tmp_path / "none.toml")]) == 1
    assert "none.toml is missing" in capsys.readouterr().err
    bad = tmp_path / "bad.toml"
    bad.write_bytes(b"\xff\xfe")
    with pytest.raises(StructureError, match="cannot be read"):
        load(bad)
    bad.write_text(section(prefix='"x"'), encoding="utf-8")
    with pytest.raises(StructureError, match="bad.toml: section 'start'"):
        load(bad)


def test_docs_that_are_not_a_folder_are_one_problem(tmp_path: Path) -> None:
    assert check(parse(GOOD), tmp_path / "none") == [f"{tmp_path / 'none'} is not a folder"]


@pytest.mark.parametrize("entries", ["[1, 2]", '["start"]', "[[1]]"])
def test_a_section_entry_that_is_not_a_table_is_refused(entries) -> None:
    with pytest.raises(StructureError, match="section 1 is not a table of keys"):
        parse(f"section = {entries}")


def test_a_page_that_is_not_utf_8_is_a_problem_not_a_crash(tmp_path: Path) -> None:
    sections = parse(GOOD)
    write_tree(tmp_path, sections)
    (tmp_path / "rooms").mkdir()
    (tmp_path / "start" / "index.md").write_bytes(b"\xff\xfe# Start here")
    (tmp_path / "index.md").write_bytes(b"# Home \xe9t\xe9")
    problems = check(sections, tmp_path)
    assert f"{tmp_path / 'start' / 'index.md'} is not UTF-8 text" in problems
    assert f"{tmp_path / 'index.md'} is not UTF-8 text" in problems
    assert any(p.endswith("rooms is not a section in the structure") for p in problems)
    assert len(problems) == 3


def test_a_folder_given_as_the_structure_is_named(tmp_path: Path, capsys) -> None:
    assert main(["--structure", str(tmp_path)]) == 1
    assert f"{tmp_path} is a folder; the structure is a file" in capsys.readouterr().err
