"""MkDocs hook for the docs site (mkdocs.yml): a link from docs/ to a file elsewhere in the repo
(`../CHANGELOG.md`, `../examples/...`) points at that file on GitHub, since the site has only docs/.
It points at the ref being built ($BRAINRC_DOCS_REF, the release tag in CI; default main), so an
older version's links match its own files. Links inside docs/ and anything in code are left
alone, so `--strict` still fails on a broken link. With no `repo_url`, links are left as written."""
import os
import posixpath
import re

# Code keeps its text as written: a fenced block (indented too, closed by a fence at least as
# long), or inline code between equal runs of backticks.
FENCE = r"^[ \t]*(?P<fence>`{3,}|~{3,}).*?^[ \t]*(?P=fence)[`~]*[ \t]*$"
INLINE = r"(?P<ticks>`+)[^`\n](?:[^\n]*?[^`\n])?(?P=ticks)(?!`)"
# A link target that leaves docs/: `](../path#anchor)`, optionally with a "title".
LINK = r"\]\((?P<target>\.\./[^)\s#]+)(?P<anchor>#[^)\s]*)?(?P<title>\s+\"[^\"]*\")?\)"
TOKEN = re.compile(rf"(?P<code>{FENCE}|{INLINE})|{LINK}", re.M | re.S)


def blob(config) -> str | None:
    repo = config.get("repo_url")
    if not repo:
        return None
    return f"{repo.rstrip('/')}/blob/{os.environ.get('BRAINRC_DOCS_REF') or 'main'}/"


def on_page_markdown(markdown, page, config, **kwargs):
    base, url = posixpath.dirname(page.file.src_uri), blob(config)
    if url is None:
        return markdown

    def rewrite(m):
        if m["code"]:
            return m[0]
        path = posixpath.normpath(posixpath.join("docs", base, m["target"]))
        if path.startswith("docs/"):
            return m[0]  # still inside docs/: MkDocs checks it
        return f"]({url}{path}{m['anchor'] or ''}{m['title'] or ''})"
    return TOKEN.sub(rewrite, markdown)
