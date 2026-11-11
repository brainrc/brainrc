"""JSON with comments (OpenCode's opencode.jsonc): read it, and change one top-level key in place
so the user's comments and layout elsewhere in the file survive."""
from __future__ import annotations

import json
import re

PUNCT = "{}[],:"
LITERAL = re.compile(r"[^\s{}\[\],:/\"]+")


def _tokens(text: str) -> list[tuple[str, int, int]]:
    """(token, start, end) for strings, punctuation and literals; whitespace and comments skipped."""
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c.isspace():
            i += 1
        elif text.startswith("//", i):
            end = text.find("\n", i)
            i = n if end == -1 else end
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            if end == -1:
                raise ValueError("unterminated comment")
            i = end + 2
        elif c == '"':
            j = i + 1
            while j < n and text[j] != '"':
                j += 2 if text[j] == "\\" else 1
            if j >= n:
                raise ValueError("unterminated string")
            out.append((text[i:j + 1], i, j + 1))
            i = j + 1
        elif c in PUNCT:
            out.append((c, i, i + 1))
            i += 1
        elif m := LITERAL.match(text, i):
            out.append((m[0], i, m.end()))
            i = m.end()
        else:
            raise ValueError(f"unexpected {c!r}")
    return out


def loads(text: str):
    """Parse JSONC: comments and trailing commas allowed."""
    toks = _tokens(text)
    kept = [t for k, t in enumerate(toks)
            if not (t[0] == "," and k + 1 < len(toks) and toks[k + 1][0] in "}]")]
    return json.loads(" ".join(t[0] for t in kept))


def _members(toks) -> tuple[list[tuple[str, int, int, int]], int]:
    """The root object's members as (key, key token index, value start index, value end index),
    and the index of its closing brace. Raises ValueError unless the root is an object."""
    if not toks or toks[0][0] != "{":
        raise ValueError("not a JSON object")
    members, k = [], 1
    while toks[k][0] != "}":
        if toks[k][0] == ",":
            k += 1
            continue
        if not toks[k][0].startswith('"') or toks[k + 1][0] != ":":
            raise ValueError("expected a key")
        key, start, depth, j = json.loads(toks[k][0]), k + 2, 0, k + 2
        while True:
            t = toks[j][0]
            depth += t in "{[" and len(t) == 1
            depth -= t in "}]" and len(t) == 1
            if depth < 0 or (depth == 0 and t == ","):
                break
            j += 1
        members.append((key, k, start, j - 1))
        k = j
    return members, k


def set_key(text: str, key: str, value) -> str:
    """text with the root object's `key` set to value (removed when value is None)."""
    toks = _tokens(text)
    members, close = _members(toks)
    found = [m for m in members if m[0] == key]
    indent = "  "
    if members:
        first = toks[members[0][1]][1]
        lead = text[text.rfind("\n", 0, first) + 1:first]
        indent = lead if lead and lead.isspace() else indent
    rendered = json.dumps(value, indent=2).replace("\n", "\n" + indent)
    if found:
        _, k, vs, ve = found[-1]
        if value is not None:
            return text[:toks[vs][1]] + rendered + text[toks[ve][2]:]
        prev, after = toks[k - 1], ve + 1
        nl = text.rfind("\n", prev[2], toks[k][1])  # cut from the key's own line, so comments above stay
        cut = nl if nl != -1 and text[nl + 1:toks[k][1]].strip() == "" else prev[2]
        if toks[after][0] == ",":
            return text[:cut] + text[toks[after][2]:]
        if prev[0] == ",":  # the last member: its comma goes too
            return text[:prev[1]] + text[prev[2]:cut] + text[toks[ve][2]:]
        return text[:cut] + text[toks[ve][2]:]
    if value is None:
        return text
    last = toks[close - 1]
    entry = f"\n{indent}{json.dumps(key)}: {rendered}"
    if last[0] == "{":
        return text[:last[2]] + entry + "\n" + text[toks[close][1]:]
    sep = "" if last[0] == "," else ","
    return text[:last[2]] + sep + entry + text[last[2]:]
