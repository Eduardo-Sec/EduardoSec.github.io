import re
import mistune
from django.utils.text import slugify


class _PortfolioRenderer(mistune.HTMLRenderer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._toc = []  # list of (level, text, anchor)

    def heading(self, text, level, **attrs):
        # Strip tags from text to build a clean anchor id
        plain = re.sub(r'<[^>]+>', '', text)
        anchor = slugify(plain)
        if level in (2, 3):
            self._toc.append((level, plain, anchor))
        return f'<h{level} id="{anchor}" style="scroll-margin-top:80px">{text}</h{level}>\n'

    def block_code(self, code, info=None, **attrs):
        lang = (info or '').strip().split()[0] if info else ''
        lang_attr = f' data-lang="{mistune.escape(lang)}"' if lang else ''
        return (
            f'<div class="highlight">'
            f'<pre><code{lang_attr}>{mistune.escape(code)}</code></pre>'
            f'</div>\n'
        )


def render_markdown(text):
    """Return (content_html, toc_html) for a markdown string."""
    renderer = _PortfolioRenderer(escape=False)
    md = mistune.create_markdown(
        renderer=renderer,
        plugins=['strikethrough', 'table', 'url'],
    )
    content_html = md(text)
    toc_html = _build_toc(renderer._toc)
    return content_html, toc_html


def _build_toc(toc):
    if not toc:
        return ''
    items = []
    for level, text, anchor in toc:
        indent = '  ' if level == 3 else ''
        items.append(f'{indent}<li><a href="#{anchor}">{text}</a></li>')
    return '<ul>\n' + '\n'.join(items) + '\n</ul>'
