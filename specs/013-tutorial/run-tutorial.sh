#!/usr/bin/env bash
# Runs every ```bash block in docs/tutorial.md, in order, on a fresh clone with a temp HOME.
# Usage: specs/013-tutorial/run-tutorial.sh [path-to-core-checkout]   (default: this repo)
set -euo pipefail
core="$(cd "${1:-$(dirname "$0")/../..}" && pwd)"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
script="$tmp/tutorial.sh"
{
  echo 'set -euxo pipefail'
  awk '/^```bash$/{on=1; next} /^```$/{if(on){on=0; print ""}; next} on' "$core/docs/tutorial.md"
} | sed "s#<this-repo>#$core#g" > "$script"
echo "== $(grep -c '' "$script") lines extracted from docs/tutorial.md"
env -u XDG_CONFIG_HOME -u CLAUDE_CONFIG_DIR -u CODEX_HOME HOME="$tmp/home" bash "$script"  # each var moves a harness
echo "== tutorial ran clean"
