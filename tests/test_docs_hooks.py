import docs_hooks

FOOTNOTE_PAGE = (
    '<p>Text with a note.<sup id="fnref:a">'
    '<a class="footnote-ref" href="#fn:a">1</a></sup> More.</p>\n'
    '<p>Second.<sup id="fnref:b">'
    '<a class="footnote-ref" href="#fn:b">2</a></sup></p>\n'
    '<div class="footnote">\n<hr />\n<ol>\n'
    '<li id="fn:a">\n<p>Note A with <em>emphasis</em>.&#160;'
    '<a class="footnote-backref" href="#fnref:a"'
    ' title="Jump back to footnote 1 in the text">&#8617;</a></p>\n</li>\n'
    '<li id="fn:b">\n<p>Note B.&#160;'
    '<a class="footnote-backref" href="#fnref:b"'
    ' title="Jump back to footnote 2 in the text">&#8617;</a></p>\n</li>\n'
    "</ol>\n</div>"
)


def test_sidenotes_moves_each_note_beside_its_reference():
    out = docs_hooks.sidenotes(FOOTNOTE_PAGE)
    assert (
        '<span class="sidenote-number"></span>'
        '<span class="sidenote">Note A with <em>emphasis</em>.</span> More.' in out
    )
    assert (
        '<span class="sidenote-number"></span>'
        '<span class="sidenote">Note B.</span></p>' in out
    )


def test_sidenotes_drops_the_footnote_block_and_backrefs():
    out = docs_hooks.sidenotes(FOOTNOTE_PAGE)
    assert 'class="footnote"' not in out
    assert "footnote-backref" not in out
    assert "&#8617;" not in out
    assert "fnref:" not in out


def test_sidenotes_leaves_a_page_without_footnotes_alone():
    html = "<p>Plain.</p>\n<table><tr><td>1</td></tr></table>"
    assert docs_hooks.sidenotes(html) == html


def test_sidenotes_keeps_a_multi_paragraph_note():
    html = (
        '<p>A.<sup id="fnref:x">'
        '<a class="footnote-ref" href="#fn:x">1</a></sup></p>\n'
        '<div class="footnote">\n<hr />\n<ol>\n<li id="fn:x">\n'
        "<p>First.</p>\n<p>Second.&#160;"
        '<a class="footnote-backref" href="#fnref:x"'
        ' title="Jump back to footnote 1 in the text">&#8617;</a></p>\n'
        "</li>\n</ol>\n</div>"
    )
    out = docs_hooks.sidenotes(html)
    assert '<span class="sidenote"><p>First.</p>\n<p>Second.</p></span>' in out


def test_scrolling_tables_wraps_each_table():
    html = (
        "<p>a</p>\n<table>\n<tr><td>1</td></tr>\n</table>\n"
        "<p>b</p>\n<table><tr><td>2</td></tr></table>"
    )
    out = docs_hooks.scrolling_tables(html)
    assert out.count('<div class="table-scroll">') == 2
    assert out.startswith('<p>a</p>\n<div class="table-scroll"><table>')
    assert out.endswith("<table><tr><td>2</td></tr></table></div>")


def test_scrolling_tables_does_not_double_wrap():
    html = '<div class="table-scroll"><table><tr><td>1</td></tr></table></div>'
    assert docs_hooks.scrolling_tables(html) == html


def test_scrolling_tables_leaves_pages_without_tables_alone():
    html = "<p>Nothing tabular.</p>"
    assert docs_hooks.scrolling_tables(html) == html
