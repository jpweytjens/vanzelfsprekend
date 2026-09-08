"""MkDocs hooks for the vanzelfsprekend site.

Pure functions over HTML and over the palette module, plus the MkDocs
event glue that calls them. Registered in `mkdocs.yml` under `hooks:`.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
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


def on_page_content(html: str, page: Page, config: MkDocsConfig, files: Files) -> str:
    """Apply the HTML rewrites to every page (MkDocs event)."""
    return sidenotes(html)
