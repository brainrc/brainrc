"""brainrc: sync this repo's skills, agents, commands, rules, and hooks into AI harnesses.

Run it with `python3 scripts/brainrc.py <command>` or `python3 -m brainrc <command>`; usage is in
`brainrc.cli`. Below are the names tests and scripts/evals.py use. Shared state such as `REPO`
lives in the module that owns it (`brainrc.config.REPO`), so patch it there.
"""
from . import cli, config, doctor, init, mcp, opencode, plan, plugin, settings, tokens, validate  # noqa: F401
from .config import (
    BACKUPS_KEPT,
    HOOKS_DIR_PLACEHOLDER,
    extensions_file,
    rendered_instructions,
    settings_home,
    tilde,
)
from .sources import (
    Source,
    frontmatter,
    load_pack,
    markdown_files,
    parse_constraint,
    render_instructions,
    rule_text,
    satisfies,
    skills,
    sources,
)
from .opencode import opencode_agent
from .plan import Link, SettingsMerge, link_target, render_fragment
from .settings import _owned, merge_settings
from .plugin import check_plugin, cmd_plugin, plugin_manifests
from .release import check_fragments, cmd_release, next_version, parse_fragment
from .tokens import always_tokens, check_budgets, cmd_tokens, estimate_tokens
from .validate import check_roles_link, cmd_validate
from .doctor import cmd_doctor, doctor_findings
from .cli import cmd_sync, cmd_update, main
