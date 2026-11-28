#!/usr/bin/env python3
"""The pack API contract (#174): print it, or freeze it when PACK_API moves.

    python3 scripts/pack_api.py            # print the live contract
    python3 scripts/pack_api.py --write    # write docs/schemas/pack-api/<PACK_API>.json

See brainrc/packapi.py and docs/packs.md#compatibility.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from brainrc.packapi import main  # noqa: E402  (needs the repo root on sys.path first)

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
