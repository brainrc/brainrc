"""A harness whose config dir moved: CLAUDE_CONFIG_DIR, CODEX_HOME or XDG_CONFIG_HOME changed
since the last apply (#110), so brainrc's links and hooks may be left at the old place. apply and
status warn when it happens, doctor while links are still there. uninstall also cleans each
harness's default dir, so only an old dir that is neither the default nor recorded is lost."""
from __future__ import annotations

from pathlib import Path

from .config import ConfigError, command, harness_home, harness_vars, load_harnesses, tilde
from .manifest import checked_manifest, read_manifest


def _home(h: dict) -> Path | None:
    try:
        return harness_home(h)
    except (TypeError, ValueError):
        return None


def _defaults() -> dict[str, dict]:
    try:
        return load_harnesses(include_disabled=True, defaults=True)
    except ConfigError:
        return {}


def move_warnings(managed: dict[str, dict]) -> list[str]:
    """For apply and status: each harness whose home differs from the one the last apply recorded."""
    recorded, defaults, out = read_manifest()["harnesses"], _defaults(), []
    for name, h in managed.items():
        old, new = _home(recorded.get(name, {})), _home(h)
        if not old or not new or old == new:
            continue
        moved = f"{name}'s config dir moved from {tilde(old)} to {tilde(new)} since the last apply"
        if old == _home(defaults.get(name, {})):
            out.append(f"{moved}. brainrc's links and hooks in {tilde(old)} stay; "
                       f"`{command('uninstall')}` removes them with the rest")
        else:
            var = " and ".join(harness_vars(name)) or "its env var"
            out.append(f"{moved}. brainrc's links and hooks in {tilde(old)} stay, and once apply records "
                       f"the new dir only `{command('uninstall')}` run with {var} set as before removes "
                       f"them (then `{command('apply')}` again)")
    return out


def left_behind(roots: list[Path]) -> list[tuple[str, Path, Path, int]]:
    """(harness, other dir, its dir now, brainrc links in the other dir) for each managed harness
    whose recorded or default dir isn't the one it reads now and still holds brainrc's links."""
    from .plan import _managed_target, link_target
    from .uninstall import _link_candidates
    recorded, defaults, out = checked_manifest()[0]["harnesses"], _defaults(), []
    for name, h in load_harnesses().items():
        now, seen = _home(h), set()
        for other in (recorded.get(name), defaults.get(name)):
            where = _home(other or {})
            if not where or where == now or where in seen:
                continue
            seen.add(where)
            links = [p for p in _link_candidates(other) if p.is_symlink()
                     and _managed_target(link_target(p), roots)]
            if links:
                out.append((name, where, now, len(links)))
    return out
