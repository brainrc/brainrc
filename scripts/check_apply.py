#!/usr/bin/env python3
"""Apply into a temporary HOME with every tool's home present, then check that brainrc keeps track
of what it wrote: status says it's in sync, doctor finds no problem, and uninstall leaves nothing
but the empty tool homes and its backups. The real HOME is never read or written.

Usage: python3 scripts/check_apply.py [--copy]
--copy sets BRAINRC_LINK_MODE=copy and git's core.symlinks=false, as a Windows machine without
Developer Mode gets them, and checks that apply made no symlink and copied Gatework's roles/. On
Windows it also checks each hook command is in the native form (brainrc/hookcmd.py), not a POSIX
shell line. CI runs it with --copy in every validate cell (#179).
Prints one PASS/FAIL line per check; exits 1 on any FAIL.
"""
import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
# Each tool's home as tests/test_brainrc.py lays them out; apply manages a tool whose home exists.
HOMES = (".claude", ".codex", ".config/opencode", ".gemini/config", ".cursor", ".copilot", ".config/devin",
         ".kiro", ".config/amp", ".junie")
# Variables that would point apply at a real config instead of the temporary HOME's.
CLEARED = ("XDG_CONFIG_HOME", "CLAUDE_CONFIG_DIR", "CODEX_HOME", "COPILOT_HOME", "KIRO_HOME", "BRAINRC_HOME",
           "BRAINRC_LINK_MODE", "GIT_CONFIG_GLOBAL", "GIT_DIR", "GIT_WORK_TREE")
failed = False


def _writable_retry(func, path, _exc):
    """Git marks its object files read-only, and Windows won't delete a read-only file."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def report(name: str, ok: bool, detail: str = "") -> None:
    global failed
    failed |= not ok
    print(f"{'PASS' if ok else 'FAIL'} {name}" + (f"\n{detail.rstrip()}" if detail and not ok else ""))


def brainrc(env: dict, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(REPO / "scripts" / "brainrc.py"), *args], env=env,
                          capture_output=True, text=True, timeout=600)


def files(home: Path) -> list[Path]:
    """Every file and link under home (the tool homes made here aside)."""
    return sorted(p for p in home.rglob("*") if p.is_symlink() or not p.is_dir())


def hook_lines(home: Path) -> list[str]:
    """Each hook command apply wrote into Codex's hooks.json, the one every machine runs."""
    path = home / ".codex" / "hooks.json"
    data = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    return [json.dumps(h) for groups in data.get("hooks", {}).values() for g in groups for h in g.get("hooks", [])]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--copy", action="store_true", help="copy instead of linking (BRAINRC_LINK_MODE=copy)")
    copy = parser.parse_args().copy
    local = sorted(p.name for p in REPO.glob("*.local.toml"))
    if local:  # a checkout's machine-local files apply to a run from it, as they do to apply
        print(f"note: this checkout's {', '.join(local)} apply to this run")
    tmp = Path(tempfile.mkdtemp(prefix="brainrc-apply-")).resolve()
    try:
        home = tmp / "home"
        for d in HOMES:
            (home / d).mkdir(parents=True)
        env = {k: v for k, v in os.environ.items() if k not in CLEARED}
        env |= {"HOME": str(home), "USERPROFILE": str(home)}  # Path.home() reads USERPROFILE on Windows
        if copy:
            env["BRAINRC_LINK_MODE"] = "copy"
            # Clone the packs as a Windows machine without Developer Mode does: each link in a pack
            # (Gatework's roles/) arrives as git's plain-file stand-in, which copy mode follows.
            gitconfig = tmp / "gitconfig"
            gitconfig.write_text("[core]\n\tsymlinks = false\n", encoding="utf-8")
            env["GIT_CONFIG_GLOBAL"] = str(gitconfig)
        result = brainrc(env, "apply")
        report("apply", result.returncode == 0, result.stdout + result.stderr)
        if copy:
            # The settings home holds the packs' own git checkouts, whose links are git's to make.
            links = [str(p.relative_to(home)) for p in files(home)
                     if p.is_symlink() and home / ".config" / "brainrc" not in p.parents]
            report("apply made no symlink", not links, "\n".join(links))
            roles = home / ".claude" / "skills" / "brainrc-gatework" / "roles"
            report("Gatework's roles/ is copied as a folder of role files",
                   roles.is_dir() and not roles.is_symlink() and any(roles.glob("*.md")),
                   f"{roles}: {'a file' if roles.is_file() else 'missing'}")
        hooks = hook_lines(home)
        report("apply wrote Codex's hooks", bool(hooks))
        if os.name == "nt":
            posix = [h for h in hooks if "commandWindows" not in h]
            report("each hook has its Windows command", not posix, "\n".join(posix))
        result = brainrc(env, "status")
        report("status is in sync", result.returncode == 0 and "Everything in sync." in result.stdout,
               result.stdout + result.stderr)
        result = brainrc(env, "doctor")
        report("doctor finds no problem", result.returncode == 0, result.stdout + result.stderr)
        result = brainrc(env, "uninstall", "--purge")
        # uninstall keeps the backups brainrc made of each settings file (*.bak-brainrc-*), by design.
        left = [str(p.relative_to(home)) for p in files(home) if ".bak-brainrc-" not in p.name]
        report("uninstall leaves nothing", result.returncode == 0 and not left,
               (result.stderr if result.returncode else "") + "\n".join(left))
    finally:
        shutil.rmtree(tmp, **{"onexc" if sys.version_info >= (3, 12) else "onerror": _writable_retry})
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
