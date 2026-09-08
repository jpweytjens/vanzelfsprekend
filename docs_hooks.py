"""MkDocs hooks for the vanzelfsprekend site.

Pure functions over HTML and over the palette module, plus the MkDocs
event glue that calls them. Registered in `mkdocs.yml` under `hooks:`.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import TYPE_CHECKING

from vanzelfsprekend import palettes

if TYPE_CHECKING:
    from collections.abc import Callable

    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files
    from mkdocs.structure.pages import Page

FOOTNOTE_BLOCK = re.compile(r'\n?<div class="footnote">.*?</div>', re.DOTALL)
FOOTNOTE_ITEM = re.compile(
    r'<li id="fn:(?P<key>[^"]+)">\s*(?P<body>.*?)\s*</li>', re.DOTALL
)
BACKREF = re.compile(r'(?:&#160;|\s)*<a class="footnote-backref"[^>]*>[^<]*</a>')
REFERENCE = re.compile(
    r'<sup id="fnref:(?P<key>[^"]+)"><a class="footnote-ref"[^>]*>\d+</a></sup>'
)
SINGLE_PARAGRAPH = re.compile(r"\A<p>(?P<inner>(?:(?!</p>).)*)</p>\Z", re.DOTALL)
TABLE = re.compile(r'(?<!<div class="table-scroll">)<table>.*?</table>', re.DOTALL)
XML_PROLOG = re.compile(r"\A(?:<\?xml[^>]*>\s*)?(?:<!DOCTYPE[^>]*>\s*)?", re.DOTALL)
SVG_SIZE = re.compile(r'\s(?:width|height)="[^"]*"')
HEX_COLOUR = re.compile(r"#[0-9a-fA-F]{6}")
IMG_TAG = re.compile(r"(?:<p>)?<img\b(?P<attrs>[^>]*?)/?>(?:</p>)?")
ATTRIBUTE = re.compile(r'(?P<name>\w+)="(?P<value>[^"]*)"')

# Pygments short class names, grouped into Alabaster's four categories.
STRING_CLASSES = ".s, .s1, .s2, .sa, .sb, .sc, .se, .sh, .si, .sx, .sr, .ss, .dl"
COMMENT_CLASSES = ".c, .c1, .cm, .cs, .ch, .cp, .cpf, .sd"
CONSTANT_CLASSES = ".m, .mi, .mf, .mh, .mo, .mb, .il, .kc"
DEFINITION_CLASSES = ".nf, .nc, .fm"

# The site's own dark counterparts to the three ink roles. If the package
# ever gains dark-ground inks, these go and both sets come from palettes.
DARK_INKS = {"--ink-data": "#dcdcdc", "--ink-text": "#9a9a9a", "--ink-line": "#666666"}

INK_TOKENS = {
    palettes.DATA_INK.lower(): "--ink-data",
    palettes.TEXT_INK.lower(): "--ink-text",
    palettes.LINE_INK.lower(): "--ink-line",
}


def sidenotes(html: str) -> str:
    """Rewrite Python-Markdown footnotes into Tufte sidenotes.

    Each footnote reference becomes an empty ``span.sidenote-number``
    followed by a ``span.sidenote`` holding the note's body; the
    footnote block at the end of the page is removed. A one-paragraph
    note is unwrapped so it flows inline in the margin; a longer note
    keeps its paragraphs. Numbering is the stylesheet's CSS counter.

    Parameters
    ----------
    html
        One page's rendered content.

    Returns
    -------
    str
        The page with sidenotes in place of footnotes, or the input
        unchanged when it has no footnote block.
    """
    block = FOOTNOTE_BLOCK.search(html)
    if block is None:
        return html
    notes: dict[str, str] = {}
    for item in FOOTNOTE_ITEM.finditer(block.group(0)):
        body = BACKREF.sub("", item.group("body")).strip()
        single = SINGLE_PARAGRAPH.match(body)
        notes[item.group("key")] = single.group("inner") if single else body

    def replace(match: re.Match[str]) -> str:
        body = notes[match.group("key")]
        return (
            f'<span class="sidenote-number"></span><span class="sidenote">{body}</span>'
        )

    without_block = html[: block.start()] + html[block.end() :]
    return REFERENCE.sub(replace, without_block)


def scrolling_tables(html: str) -> str:
    """Wrap every table in ``div.table-scroll`` so a wide one scrolls inside itself.

    A table already wrapped is left alone.

    Parameters
    ----------
    html
        One page's rendered content.

    Returns
    -------
    str
        The page with each bare table wrapped.
    """
    return TABLE.sub(lambda m: f'<div class="table-scroll">{m.group(0)}</div>', html)


def palette_css() -> str:
    """Write the colour tokens and the syntax rules from the palette module.

    Light mode takes its code colours from Tol's muted scheme and its
    soft ink from Tol's dark grey; dark mode takes its code colours from
    Tol's light scheme. The three ink roles get a token each so an
    inlined figure can follow the page's ground. Only four token
    categories are coloured: strings, comments and docstrings,
    constants, definitions. Everything else stays body ink.

    Returns
    -------
    str
        A complete stylesheet.
    """
    light = {
        "--ink-soft": palettes.DARK["grey"],
        "--link": "#3a6ea5",
        "--code-string": palettes.MUTED["wine"],
        "--code-comment": palettes.MUTED["green"],
        "--code-constant": palettes.MUTED["purple"],
        "--code-definition": palettes.MUTED["indigo"],
        "--ink-data": palettes.DATA_INK,
        "--ink-text": palettes.TEXT_INK,
        "--ink-line": palettes.LINE_INK,
    }
    dark = {
        "--ink-soft": "#9a9a9a",
        "--link": palettes.LIGHT["light_blue"],
        "--code-string": palettes.LIGHT["pink"],
        "--code-comment": palettes.LIGHT["mint"],
        "--code-constant": palettes.LIGHT["light_cyan"],
        "--code-definition": palettes.LIGHT["light_blue"],
        **DARK_INKS,
    }

    def block(tokens: dict[str, str]) -> str:
        return "".join(f"  {name}: {value};\n" for name, value in tokens.items())

    return (
        "/* Generated by docs_hooks.palette_css from vanzelfsprekend.palettes."
        " Do not edit. */\n"
        f":root {{\n{block(light)}}}\n"
        f"@media (prefers-color-scheme: dark) {{\n  :root {{\n{block(dark)}  }}\n}}\n"
        f"{STRING_CLASSES} {{ color: var(--code-string); }}\n"
        f"{COMMENT_CLASSES} {{ color: var(--code-comment); font-style: italic; }}\n"
        f"{CONSTANT_CLASSES} {{ color: var(--code-constant); }}\n"
        f"{DEFINITION_CLASSES} {{ color: var(--code-definition); font-weight: 600; }}\n"
    )


def on_files(files: Files, config: MkDocsConfig) -> Files:
    """Add the generated palette stylesheet to the build (MkDocs event)."""
    from mkdocs.structure.files import File

    files.append(File.generated(config, "palette.css", content=palette_css()))
    return files


def ink_tokens(svg: str) -> str:
    """Prepare a matplotlib SVG for inlining with the page's ink tokens.

    The three ink roles become CSS variables so the figure follows the
    page's ground; every other colour is left as drawn. The XML prolog
    goes, and so do the fixed ``width`` and ``height`` on the root, so
    the stylesheet sizes the figure by its ``viewBox``.

    Parameters
    ----------
    svg
        The file's text as matplotlib wrote it.

    Returns
    -------
    str
        An ``<svg>`` element ready to drop into HTML.
    """
    body = XML_PROLOG.sub("", svg, count=1)
    root_end = body.index(">") + 1
    root = SVG_SIZE.sub("", body[:root_end])
    rest = HEX_COLOUR.sub(
        lambda m: (
            f"var({INK_TOKENS[m.group(0).lower()]})"
            if m.group(0).lower() in INK_TOKENS
            else m.group(0)
        ),
        body[root_end:],
    )
    return root + rest


def inline_svg(html: str, read: Callable[[str], str]) -> str:
    """Replace each ``<img>`` pointing at an SVG with the file's content.

    Parameters
    ----------
    html
        One page's rendered content.
    read
        Returns the SVG text for a ``src`` as the page spells it.

    Returns
    -------
    str
        The page with SVG figures inlined; PNG images are untouched.
    """

    def replace(match: re.Match[str]) -> str:
        attrs = dict(ATTRIBUTE.findall(match.group("attrs")))
        src = attrs.get("src", "")
        if not src.endswith(".svg"):
            return match.group(0)
        svg = ink_tokens(read(src))
        return svg.replace(
            "<svg ", f'<svg role="img" aria-label="{attrs.get("alt", "")}" ', 1
        )

    return IMG_TAG.sub(replace, html)


def figure_reader(docs_dir: Path, dest_uri: str) -> Callable[[str], str]:
    """Return a reader for the paths one page spells in its ``src`` attributes.

    MkDocs rewrites every ``src`` to be relative to the page's built
    location before this hook sees it, so the tutorial's
    ``../../figures/x.svg`` and the home page's ``figures/x.svg`` name
    the same file. A media file sits at the same relative path under the
    documentation directory as under the site, so walking the rewritten
    ``src`` from the page's destination finds the source file.

    Parameters
    ----------
    docs_dir
        The build's documentation directory.
    dest_uri
        The page's path within the built site, ``page.file.dest_uri``.

    Returns
    -------
    Callable[[str], str]
        Reads one ``src`` and returns the file's text.
    """
    base = (docs_dir / dest_uri).parent

    def read(src: str) -> str:
        return (base / src).resolve().read_text(encoding="utf-8")

    return read


def on_page_content(html: str, page: Page, config: MkDocsConfig, files: Files) -> str:
    """Apply the HTML rewrites to every page (MkDocs event)."""
    read = figure_reader(Path(config["docs_dir"]), page.file.dest_uri)
    return scrolling_tables(inline_svg(sidenotes(html), read))
