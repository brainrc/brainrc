#!/usr/bin/env python3
"""Tiny CLI used to exercise the spec-agent workflow."""
import argparse
import sys


def greet(name: str) -> str:
    return f"Hello, {name}!"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Print a greeting.")
    parser.add_argument("name", nargs="?", default="world")
    args = parser.parse_args(argv)
    print(greet(args.name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
