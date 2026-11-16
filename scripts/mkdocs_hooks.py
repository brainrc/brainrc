"""MkDocs hook for the docs site (mkdocs.yml): a link from docs/ to a file elsewhere in the repo
(`../CHANGELOG.md`, `../examples/...`) points at that file on GitHub, since the site has only docs/,
and a link to the `schemas/` folder points at the schemas page. Other links inside docs/ are left
for MkDocs, so `--strict` still fails on a broken one."""
import posixpath
import re

BLOB = "https://github.com/brainrc/brainrc/blob/main/"
LINK = re.compile(r"\]\((?P<target>\.\./[^)\s#]+)(?P<anchor>#[^)\s]*)?\)")


def on_page_markdown(markdown, page, **kwargs):
    base = posixpath.dirname(page.file.src_uri)

    def outside(m):
        path = posixpath.normpath(posixpath.join("docs", base, m["target"]))
        if path.startswith("docs/"):
            return m[0]  # still inside docs/: MkDocs checks it
        return f"]({BLOB}{path}{m['anchor'] or ''})"
    return LINK.sub(outside, markdown).replace("](schemas/)", "](schemas.md)")
